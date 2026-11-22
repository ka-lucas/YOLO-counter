"""Interface web mínima (FastAPI): envia um vídeo ou informa uma URL de câmera, acompanha o
vídeo anotado ao vivo (MJPEG) e baixa o relatório da contagem.

Uma contagem por vez. Rodar com: yolo-counter serve
"""
from __future__ import annotations

import os
import shutil
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

import cv2
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

from .geometry import Line
from .pipeline import CountConfig, iter_count

STATIC = Path(__file__).parent / "static"
UPLOAD_DIR = Path(os.environ.get("YOLO_COUNTER_UPLOADS", tempfile.gettempdir())) / "yolo-counter"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_MODEL = os.environ.get("YOLO_COUNTER_MODEL", "yolo11n.pt")


@dataclass
class Job:
    config: CountConfig
    status: str = "starting"      # starting | running | finished | stopped | error
    error: str | None = None
    frame: int = 0
    totals: dict = field(default_factory=lambda: {"in": 0, "out": 0, "total": 0, "by_class": {}})
    events: list = field(default_factory=list)
    jpeg: bytes | None = None
    started_at: float = field(default_factory=time.time)
    stop: threading.Event = field(default_factory=threading.Event)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def run(self) -> None:
        try:
            self.status = "running"
            for r in iter_count(self.config, stop=self.stop):
                ok, buf = cv2.imencode(".jpg", r.image, [cv2.IMWRITE_JPEG_QUALITY, 80])
                with self.lock:
                    self.frame, self.totals = r.index, r.totals
                    self.events.extend(e.to_dict() for e in r.new_events)
                    if ok:
                        self.jpeg = buf.tobytes()
            self.status = "stopped" if self.stop.is_set() else "finished"
        except Exception as exc:  # erro vai para a interface em vez de derrubar o servidor
            self.status, self.error = "error", str(exc)

    def snapshot(self) -> dict:
        with self.lock:
            return {"status": self.status, "error": self.error, "frame": self.frame, "totals": self.totals,
                    "events": list(self.events), "source": str(self.config.source),
                    "elapsed_s": round(time.time() - self.started_at, 1)}


app = FastAPI(title="YOLO Counter")
_job: Job | None = None


def _start(cfg: CountConfig) -> Job:
    global _job
    if _job and _job.status in {"starting", "running"}:
        raise HTTPException(409, "já existe uma contagem em andamento; pare-a antes de começar outra")
    _job = Job(cfg)
    threading.Thread(target=_job.run, daemon=True).start()
    return _job


def _config(source: str, line: str | None, classes: str | None, conf: float) -> CountConfig:
    try:
        parsed_line = Line.parse(line) if line else None
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    class_list = [c.strip() for c in classes.split(",") if c.strip()] if classes else None
    return CountConfig(source=source, model=DEFAULT_MODEL, line=parsed_line, classes=class_list, conf=conf)


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.post("/api/jobs/upload")
async def start_from_upload(file: UploadFile = File(...), line: str | None = Form(None),
                            classes: str | None = Form(None), conf: float = Form(0.35)):
    suffix = Path(file.filename or "video.mp4").suffix.lower()
    if suffix not in {".mp4", ".avi", ".mov", ".mkv", ".webm"}:
        raise HTTPException(415, "formato não suportado; use mp4, avi, mov, mkv ou webm")
    dest = UPLOAD_DIR / f"{int(time.time())}{suffix}"
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    return _start(_config(str(dest), line, classes, conf)).snapshot()


@app.post("/api/jobs/stream")
def start_from_stream(source: str = Form(...), line: str | None = Form(None),
                      classes: str | None = Form(None), conf: float = Form(0.35)):
    return _start(_config(source, line, classes, conf)).snapshot()


@app.get("/api/jobs/current")
def current():
    if _job is None:
        return JSONResponse({"status": "idle"})
    return _job.snapshot()


@app.post("/api/jobs/current/stop")
def stop():
    if _job is None:
        raise HTTPException(404, "nenhuma contagem")
    _job.stop.set()
    return {"status": "stopping"}


@app.get("/api/jobs/current/video")
def video():
    if _job is None:
        raise HTTPException(404, "nenhuma contagem")

    def frames():
        last = None
        while True:
            job = _job
            if job is None:
                return
            with job.lock:
                jpeg = job.jpeg
            if jpeg is not None and jpeg is not last:
                last = jpeg
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"
            if job.status not in {"starting", "running"}:
                return
            time.sleep(0.03)

    return StreamingResponse(frames(), media_type="multipart/x-mixed-replace; boundary=frame")
