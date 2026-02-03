import cv2
import time
import threading
import torch
import os
import signal
import sys

# Configurações críticas para produção
os.environ['YOLO_VERBOSE'] = 'False'
os.environ['ULTRALYTICS_SETTINGS'] = '{}'
os.environ['TORCH_FORCE_WEIGHTS_ONLY_LOAD'] = '0'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'

# Monkey patch para desabilitar signal handlers do ultralytics
def dummy_signal_handler(*args, **kwargs):
    pass

# Substituir signal.signal antes de importar ultralytics
original_signal = signal.signal
signal.signal = dummy_signal_handler

try:
    from ultralytics import YOLO
    # Restaurar signal original após import
    signal.signal = original_signal
except ImportError:
    YOLO = None
    signal.signal = original_signal

class VideoCounterProcessor:
    """
    Conta IN/OUT quando o centroide do objeto cruza uma linha horizontal.
    Usa YOLO + tracking (ByteTrack) para manter IDs.
    """

    def __init__(self, video_path: str, config, camera=None):
        self.video_path = str(video_path)
        self.config = config
        self.camera = camera  # Referência da câmera

        self.is_running = False
        self.is_paused = False

        self.latest_jpeg = None
        self.counts = {"in": 0, "out": 0}

        self._thread = None
        self._lock = threading.Lock()

        self.cap = None
        self.fps = 30.0

        # linha vinda do front (0..1)
        self.line_y_norm = getattr(config, "line_y_norm", 0.5)
        print(f"Processor inicializado com linha: {self.line_y_norm}")

        # YOLO model - inicializar apenas quando necessário
        self.model = None
        self.model_path = self.config.model_path

        # memória para contagem por ID
        self._last_side_by_id = {}      # id -> -1 (acima) / +1 (abaixo)
        self._counted_recently = {}     # id -> cooldown frames
        self._frame_idx = 0

        # ajuste: permite “debounce” (evita contar várias vezes no mesmo bicho)
        self._cooldown_frames = 20

        # Usar classe específica da câmera se disponível
        if camera and hasattr(camera, 'detection_class'):
            self.classes = [camera.detection_class]  # Apenas a classe da câmera
        else:
            self.classes = getattr(config, "classes", None)  # ex: [0] ou None

        # confiança
        self.conf = float(getattr(config, "conf_thres", 0.25))

        # resize
        self.resize_scale = float(getattr(config, "resize_scale", 1.0))

    def set_line_y_norm(self, y_norm: float):
        with self._lock:
            old_value = self.line_y_norm
            self.line_y_norm = max(0.0, min(1.0, float(y_norm)))
            print(f"Linha atualizada: {old_value} -> {self.line_y_norm}")

    def start(self):
        self.is_running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False

    def stop(self):
        self.is_running = False
        if self.cap:
            self.cap.release()

    def _side(self, cy: float, line_y: float) -> int:
        # -1 acima, +1 abaixo
        return -1 if cy < line_y else 1

    def _loop(self):
        # Verificar se YOLO está disponível
        if YOLO is None:
            print("YOLO não disponível")
            self.is_running = False
            return
        
        # Inicializar modelo YOLO na thread de processamento
        if self.model is None:
            try:
                torch.set_num_threads(1)
                self.model = YOLO(self.model_path)
            except Exception as e:
                print(f"Erro ao carregar modelo YOLO: {e}")
                self.is_running = False
                return
        
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            self.is_running = False
            return

        self.fps = float(self.cap.get(cv2.CAP_PROP_FPS) or 30.0)

        while self.is_running:
            if self.is_paused:
                time.sleep(0.05)
                continue

            ok, frame = self.cap.read()
            if not ok:
                # loop no vídeo (teste)
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            if self.resize_scale != 1.0:
                frame = cv2.resize(frame, None, fx=self.resize_scale, fy=self.resize_scale)

            h, w = frame.shape[:2]

            with self._lock:
                line_y = int(self.line_y_norm * h)

            # desenha a linha no frame
            cv2.line(frame, (0, line_y), (w - 1, line_y), (0, 255, 0), 2)

            # tracking com persistência (muito importante!)
            results = self.model.track(
                frame,
                conf=self.conf,
                classes=self.classes,
                persist=True,
                verbose=False
            )

            self._frame_idx += 1

            # reduz cooldown
            to_del = []
            for k, v in self._counted_recently.items():
                nv = v - 1
                if nv <= 0:
                    to_del.append(k)
                else:
                    self._counted_recently[k] = nv
            for k in to_del:
                del self._counted_recently[k]
            
            r = results[0]
            if r.boxes is not None and r.boxes.xyxy is not None:
                boxes = r.boxes.xyxy.cpu().numpy()
                ids = None
                
                # Debug: mostrar quantas detecções
                if len(boxes) > 0 and self._frame_idx % 30 == 0:  # A cada 30 frames
                    print(f"Frame {self._frame_idx}: {len(boxes)} detecções, classes filtradas: {self.classes}")

                # ids existem quando o tracker está funcionando
                if r.boxes.id is not None:
                    ids = r.boxes.id.cpu().numpy().astype(int)

                for i, b in enumerate(boxes):
                    x1, y1, x2, y2 = b.tolist()
                    cx = (x1 + x2) / 2.0
                    cy = (y1 + y2) / 2.0

                    # desenha bbox/centroide
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 2)
                    cv2.circle(frame, (int(cx), int(cy)), 3, (0, 0, 255), -1)

                    if ids is None:
                        # Sem ID consistente não dá pra contar cruzamento direito
                        print(f"Frame {self._frame_idx}: Sem IDs de tracking - objeto detectado mas não rastreado")
                        continue

                    tid = int(ids[i])
                    
                    # Debug: mostrar posição do objeto em relação à linha
                    side_text = "acima" if cy < line_y else "abaixo"
                    if self._frame_idx % 30 == 0:  # A cada 30 frames
                        print(f"ID {tid}: cy={cy:.1f}, linha={line_y}, {side_text}")

                    prev_side = self._last_side_by_id.get(tid)
                    curr_side = self._side(cy, line_y)
                    self._last_side_by_id[tid] = curr_side

                    # se não tinha histórico ainda, continua
                    if prev_side is None:
                        print(f"ID {tid}: Primeiro frame detectado, lado {curr_side}")
                        continue

                    # cruzou a linha? (mudou lado)
                    if prev_side != curr_side:
                        # debounce
                        if tid in self._counted_recently:
                            print(f"ID {tid}: Cruzamento ignorado (debounce ativo)")
                            continue

                        # define direção
                        # -1->+1: atravessou de cima pra baixo (OUT por exemplo)
                        # +1->-1: baixo pra cima (IN por exemplo)
                        if prev_side == -1 and curr_side == 1:
                            self.counts["out"] += 1
                            print(f"OUT: ID {tid} cruzou linha (cima->baixo) - Total OUT: {self.counts['out']}")
                            from .manager import counter_manager
                            counter_manager.add_event("OUT", -1, track_id=tid)      
                        elif prev_side == 1 and curr_side == -1:
                            self.counts["in"] += 1
                            print(f"IN: ID {tid} cruzou linha (baixo->cima) - Total IN: {self.counts['in']}")
                            counter_manager.add_event("IN", +1, track_id=tid)

                        self._counted_recently[tid] = self._cooldown_frames
                
                # TESTE: Incrementar contador a cada 60 frames para testar comunicação
                if self._frame_idx % 60 == 0:
                    self.counts["in"] += 1
                    print(f"TESTE: Incrementando IN para testar - Total: {self.counts['in']}")

            # escreve contadores no frame
            class_name = ""
            if self.camera and hasattr(self.camera, 'detection_class_name'):
                class_name = f" ({self.camera.detection_class_name})"
            
            # Debug info
            debug_info = f"Detections: {len(boxes) if r.boxes is not None and r.boxes.xyxy is not None else 0}"
            if self.classes:
                debug_info += f" | Class: {self.classes[0]}"
            
            cv2.putText(frame, f"IN: {self.counts['in']}  OUT: {self.counts['out']}{class_name}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,255,255), 2)
            cv2.putText(frame, debug_info,
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)

            ok2, jpg = cv2.imencode(".jpg", frame)
            if ok2:
                self.latest_jpeg = jpg.tobytes()

            time.sleep(1.0 / max(self.fps, 1.0))
