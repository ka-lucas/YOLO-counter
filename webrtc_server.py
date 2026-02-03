# webrtc_server.py - Versão otimizada para redes instáveis
import asyncio
import cv2
from aiortc import RTCPeerConnection, VideoStreamTrack, RTCSessionDescription
from aiortc.contrib.media import MediaRelay
from av import VideoFrame
from aiohttp import web
from aiohttp.web_middlewares import middleware
import json
import logging
import traceback
import numpy as np

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
# logging.getLogger("aiortc").setLevel(logging.WARNING)
# logging.getLogger("aioice").setLevel(logging.WARNING)  # Silencia warnings ICE

pcs = set()
relay = MediaRelay()


class CameraStreamTrack(VideoStreamTrack):
    def __init__(self, rtsp_url):
        super().__init__()
        self.rtsp_url = rtsp_url
        self.cap = None
        self.frame_count = 0
        self.last_valid_frame = None  # Cache do último frame válido
        self.consecutive_failures = 0
        self.max_failures = 10
        self._initialize_capture()

    def _initialize_capture(self):
        """Inicializa captura com configurações robustas para rede instável"""
        try:
            logger.info(f"Inicializando captura: {self.rtsp_url}")

            # Libera captura anterior se existir
            if self.cap:
                self.cap.release()

            self.cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)

            # Configurações otimizadas para rede instável
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Buffer mínimo
            self.cap.set(cv2.CAP_PROP_FPS, 15)  # Limita FPS para reduzir banda

            # Timeout mais agressivo (5s ao invés de 30s)
            self.cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
            self.cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)

            if not self.cap.isOpened():
                raise Exception(f"Falha ao conectar em {self.rtsp_url}")

            # Testa primeira leitura
            ret, frame = self.cap.read()
            if not ret or frame is None:
                raise Exception(f"Não foi possível ler frame inicial")

            # Redimensiona se muito grande (economiza banda no WebRTC)
            h, w = frame.shape[:2]
            if w > 1920 or h > 1080:
                scale = min(1920 / w, 1080 / h)
                new_w, new_h = int(w * scale), int(h * scale)
                frame = cv2.resize(frame, (new_w, new_h))
                logger.info(f"Frame redimensionado: {w}x{h} -> {new_w}x{new_h}")

            self.last_valid_frame = frame
            logger.info(f"✓ Conectado: {self.rtsp_url} - Frame: {frame.shape}")

        except Exception as e:
            logger.error(f"Erro ao inicializar câmera: {e}")
            raise

    async def recv(self):
        pts, time_base = await self.next_timestamp()

        # Reconecta se necessário
        if not self.cap or not self.cap.isOpened():
            logger.warning("Reconectando câmera...")
            try:
                self._initialize_capture()
                self.consecutive_failures = 0
            except Exception as e:
                logger.error(f"Falha na reconexão: {e}")
                # Retorna último frame válido se reconexão falhar
                if self.last_valid_frame is not None:
                    return self._create_video_frame(
                        self.last_valid_frame, pts, time_base
                    )
                await asyncio.sleep(1)
                return await self.recv()

        # Tenta ler frame
        ret, frame = self.cap.read()

        if not ret or frame is None:
            self.consecutive_failures += 1
            logger.warning(
                f"Frame perdido ({self.consecutive_failures}/{self.max_failures})"
            )

            # Se muitas falhas consecutivas, reconecta
            if self.consecutive_failures >= self.max_failures:
                logger.error("Muitas falhas, forçando reconexão...")
                try:
                    self._initialize_capture()
                    self.consecutive_failures = 0
                except:
                    pass

            # Retorna último frame válido (evita congelamento)
            if self.last_valid_frame is not None:
                return self._create_video_frame(self.last_valid_frame, pts, time_base)

            await asyncio.sleep(0.03)
            return await self.recv()

        # Frame válido recebido
        self.consecutive_failures = 0
        self.frame_count += 1

        # Redimensiona se necessário
        h, w = frame.shape[:2]
        if w > 1920 or h > 1080:
            scale = min(1920 / w, 1080 / h)
            frame = cv2.resize(frame, (int(w * scale), int(h * scale)))

        self.last_valid_frame = frame.copy()

        if self.frame_count % 30 == 0:
            logger.info(f"✓ {self.frame_count} frames processados")

        return self._create_video_frame(frame, pts, time_base)

    def _create_video_frame(self, frame, pts, time_base):
        """Cria VideoFrame a partir de array numpy"""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        video_frame = VideoFrame.from_ndarray(frame_rgb, format="rgb24")
        video_frame.pts = pts
        video_frame.time_base = time_base
        return video_frame

    def stop(self):
        """Libera recursos"""
        logger.info(f"Parando track - Total frames: {self.frame_count}")
        if self.cap:
            self.cap.release()
        self.last_valid_frame = None


async def offer(request):
    logger.info(f"=== Nova requisição: {request.method} {request.path} ===")

    try:
        params = await request.json()
        offer_data = params.get("offer")
        rtsp_url = params.get("rtsp_url")

        # Validações
        if not rtsp_url:
            return web.Response(
                status=400,
                content_type="application/json",
                text=json.dumps({"error": "rtsp_url é obrigatório"}),
            )

        if not offer_data or "sdp" not in offer_data or "type" not in offer_data:
            return web.Response(
                status=400,
                content_type="application/json",
                text=json.dumps({"error": "offer deve conter sdp e type"}),
            )

        logger.info(f"RTSP URL: {rtsp_url}")

        # Cria PeerConnection com configurações otimizadas
        pc = RTCPeerConnection()
        pcs.add(pc)
        logger.info(f"PeerConnection criada (total: {len(pcs)})")

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            logger.info(f"[PC] Connection state -> {pc.connectionState}")
            if pc.connectionState in ["failed", "closed"]:
                await pc.close()
                pcs.discard(pc)

        @pc.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange():
            logger.info(f"[PC] ICE state -> {pc.iceConnectionState}")

        # Cria track da câmera
        try:
            logger.info("Criando CameraStreamTrack...")
            camera = CameraStreamTrack(rtsp_url)
            pc.addTrack(camera)
            logger.info("✓ Track adicionada")

        except Exception as e:
            logger.error(f"Erro ao adicionar track: {e}")
            await pc.close()
            pcs.discard(pc)
            return web.Response(
                status=500,
                content_type="application/json",
                text=json.dumps({"error": f"Erro ao conectar câmera: {str(e)}"}),
            )

        # Processa WebRTC
        try:
            offer_desc = RTCSessionDescription(
                sdp=offer_data["sdp"], type=offer_data["type"]
            )
            await pc.setRemoteDescription(offer_desc)

            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)

            response_data = {
                "answer": {
                    "sdp": pc.localDescription.sdp,
                    "type": pc.localDescription.type,
                }
            }

            logger.info("=== Resposta enviada ===")
            return web.Response(
                content_type="application/json", text=json.dumps(response_data)
            )

        except Exception as e:
            logger.error(f"Erro WebRTC: {e}")
            await pc.close()
            pcs.discard(pc)
            return web.Response(
                status=500,
                content_type="application/json",
                text=json.dumps({"error": f"Erro WebRTC: {str(e)}"}),
            )

    except Exception as e:
        logger.error(f"Erro geral: {e}")
        logger.error(traceback.format_exc())
        return web.Response(
            status=500,
            content_type="application/json",
            text=json.dumps({"error": str(e)}),
        )


@middleware
async def cors_middleware(request, handler):
    """Middleware CORS"""
    if request.method == "OPTIONS":
        response = web.Response()
    else:
        try:
            response = await handler(request)
        except web.HTTPException as ex:
            response = ex
        except Exception as e:
            logger.error(f"Erro no middleware: {e}")
            response = web.Response(
                status=500,
                text=json.dumps({"error": str(e)}),
                content_type="application/json",
            )

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS, GET"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


async def health(request):
    """Health check"""
    return web.Response(
        text=json.dumps({"status": "ok", "active_connections": len(pcs)}),
        content_type="application/json",
    )


async def on_shutdown(app):
    """Limpa conexões"""
    logger.info(f"Encerrando {len(pcs)} conexões...")
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()


app = web.Application(middlewares=[cors_middleware])
app.router.add_post("/offer", offer)
app.router.add_get("/", health)
app.router.add_get("/health", health)
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("WebRTC Server - Otimizado para redes instáveis")
    logger.info("Porta: 8080")
    logger.info("=" * 60)
    web.run_app(app, host="0.0.0.0", port=8887)
WEBRTC_SERVER_URL = "http://192.168.0.43:8887"
