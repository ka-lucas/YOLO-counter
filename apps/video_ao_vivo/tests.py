import tempfile
import time
from pathlib import Path

import cv2
import numpy as np
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from apps.cameras.models import Camera
from .services.contador.config import CounterConfig
from .services.contador.processor import VideoCounterProcessor

MODEL = str(Path(__file__).resolve().parents[2] / "models" / "yolov8n.pt")


def make_video(path, frames=40, fps=20):
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (160, 120))
    for i in range(frames):
        frame = np.zeros((120, 160, 3), dtype=np.uint8)
        cv2.putText(frame, str(i), (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        writer.write(frame)
    writer.release()


def wait_for(cond, timeout=60):
    end = time.time() + timeout
    while time.time() < end:
        if cond():
            return True
        time.sleep(0.05)
    return False


class UploadTests(TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.user = get_user_model().objects.create_user(email="t@example.com", password="x")
        self.client.force_login(self.user)

    def tearDown(self):
        self.tmp.cleanup()

    def test_pagina_mostra_upload(self):
        resp = self.client.get("/video-ao-vivo/")
        self.assertContains(resp, 'id="btnUpload"')
        self.assertContains(resp, "/video-ao-vivo/api/upload/")

    def test_upload_cria_camera_oculta(self):
        src = Path(self.tmp.name) / "clip.mp4"
        make_video(src)
        with override_settings(MEDIA_ROOT=self.tmp.name):
            resp = self.client.post("/video-ao-vivo/api/upload/", {
                "video": SimpleUploadedFile("clip.mp4", src.read_bytes(), content_type="video/mp4"),
                "detection_class": "19",
            })
        self.assertEqual(resp.status_code, 200, resp.content)
        cam = Camera.objects.get(id=resp.json()["camera_id"])
        self.assertEqual(cam.location, Camera.UPLOAD_LOCATION)
        self.assertFalse(cam.is_active)
        self.assertEqual(cam.detection_class_name, "cow")
        self.assertTrue(Path(cam.rtsp_url).exists())

    def test_upload_rejeita_extensao_e_arquivo_invalido(self):
        with override_settings(MEDIA_ROOT=self.tmp.name):
            bad_ext = self.client.post("/video-ao-vivo/api/upload/", {
                "video": SimpleUploadedFile("x.exe", b"abc"), "detection_class": "0"})
            not_video = self.client.post("/video-ao-vivo/api/upload/", {
                "video": SimpleUploadedFile("x.mp4", b"nao sou video"), "detection_class": "0"})
        self.assertEqual(bad_ext.status_code, 400)
        self.assertEqual(not_video.status_code, 400)
        self.assertFalse(Camera.objects.exists())


class ProcessorPauseTests(TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)  # roda depois do stop do processador (LIFO)
        self.video = Path(self.tmp.name) / "clip.mp4"
        make_video(self.video)

    def _processor(self, loop):
        p = VideoCounterProcessor(self.video, CounterConfig(model_path=MODEL), loop=loop)
        p.start()

        def stop():
            p.stop()
            p._thread.join(timeout=10)
        self.addCleanup(stop)
        return p

    def test_pausa_devolve_quadro_exato_e_congela(self):
        p = self._processor(loop=True)
        self.assertTrue(wait_for(lambda: p.frame_pos >= 3))
        info = p.pause()
        self.assertIsNotNone(info)
        seq = p.jpeg_seq
        time.sleep(0.5)
        # nada avança depois da pausa: o quadro devolvido é o último processado
        self.assertEqual(info["frame"], p.frame_pos)
        self.assertEqual(seq, p.jpeg_seq)
        p.resume()
        self.assertIsNone(p.paused_at)
        self.assertTrue(wait_for(lambda: p.frame_pos != info["frame"]))

    def test_video_enviado_termina_no_ultimo_quadro(self):
        p = self._processor(loop=False)
        self.assertTrue(wait_for(lambda: p.finished))
        self.assertEqual(p.paused_at["frame"], p.total_frames)
        p.resume()  # não recomeça depois do fim
        self.assertTrue(p.is_paused)
