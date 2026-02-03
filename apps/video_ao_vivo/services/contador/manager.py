import threading
from .processor import VideoCounterProcessor
from collections import deque
import time
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
from django.conf import settings

class CounterManager:
    def __init__(self):
        self.processor = None
        self.lock = threading.Lock()
        self._events = deque(maxlen=300)  # mantém últimos 300 eventos
        self._event_id = 0
        self.current_session = None
        self.log_file = None
        self._saved_line_y_norm = 0.5  # Preservar posição da linha entre reinicializações

    def start(self, camera, user, config=None):
        """Inicia contador com uma câmera específica"""
        with self.lock:
            if self.processor and self.processor.is_running:
                return
            
            # Criar sessão no banco
            self._create_session(camera, user)
            
            # Usar modelo da câmera ou modelo padrão
            model_path, model_config = self._get_model_path_for_camera(camera)
            
            # Criar config se não fornecido
            if config is None:
                from .config import CounterConfig
                # Usar confiança do modelo ou padrão
                confidence = model_config.confidence_threshold if model_config else 0.25
                config = CounterConfig(
                    model_path=model_path,
                    conf_thres=confidence,
                    resize_scale=1.0,
                    device="cpu",
                    line_y_norm=self._saved_line_y_norm  # Usar posição salva
                )
            else:
                # Atualizar model_path no config existente
                config.model_path = model_path
                config.line_y_norm = self._saved_line_y_norm  # Usar posição salva
            
            # Usar URL da câmera
            video_source = camera.primary_url
            
            self.processor = VideoCounterProcessor(video_source, config, camera)
            self.processor.start()
    
    def _get_model_path_for_camera(self, camera):
        """Obtém o caminho do modelo para a câmera e retorna (path, model_config)"""
        from pathlib import Path
        from django.conf import settings
        
        # Tentar modelo da câmera primeiro
        if camera.model_config and camera.model_config.model_file:
            try:
                # Usar o caminho do FileField (já aponta para o storage correto)
                model_path = camera.model_config.model_file.path
                if self._validate_model(model_path):
                    return model_path, camera.model_config
            except (ValueError, AttributeError):
                pass
        
        # Tentar modelo ativo global
        from apps.configuracao.models import ModelConfiguration
        active_model = ModelConfiguration.objects.filter(is_active=True).first()
        if active_model and active_model.model_file:
            try:
                # Usar o caminho do FileField
                model_path = active_model.model_file.path
                if self._validate_model(model_path):
                    return model_path, active_model
            except (ValueError, AttributeError):
                pass
        
        # Fallback para modelo padrão
        base_dir = Path(settings.BASE_DIR)
        # Tentar modelo oficial primeiro
        official_model = base_dir / "models" / "yolov8n_official.pt"
        if official_model.exists() and self._validate_model(str(official_model)):
            return str(official_model), None
        
        # Fallback final
        default_model = base_dir / "models" / "yolov8n.pt"
        if default_model.exists() and self._validate_model(str(default_model)):
            return str(default_model), None
        
        # Último recurso - modelo YOLO padrão (será baixado automaticamente)
        return "yolov8n.pt", None
    
    def _validate_model(self, model_path):
        """Valida se o modelo é compatível"""
        try:
            # Verificar se o arquivo existe
            if not os.path.exists(model_path):
                return False
            
            from ultralytics import YOLO
            # Tenta carregar o modelo para verificar compatibilidade
            model = YOLO(model_path)
            del model  # Libera memória
            return True
        except Exception:
            return False

    def pause(self):
        with self.lock:
            if self.processor: self.processor.pause()

    #def add_event(self, kind: str, delta: int, track_id: int | None = None):]
    def add_event(self, kind: str, delta: int, track_id: Optional[int] = None):
        # kind: "IN" ou "OUT"
        self._event_id += 1
        event = {
            "id": self._event_id,
            "ts": time.time(),
            "kind": kind,
            "delta": delta,
            "track_id": track_id,
        }
        self._events.append(event)
        
        # Salvar no log
        self._log_event(event)

    def get_events_after(self, after_id: int):
        return [e for e in self._events if e["id"] > after_id]

    def resume(self):
        with self.lock:
            if self.processor: self.processor.resume()

    def stop(self):
        with self.lock:
            if self.processor: 
                self.processor.stop()
                # Finalizar sessão
                self._end_session()
            self.processor = None
    
    def _create_session(self, camera, user):
        """Cria sessão de contagem e arquivo de log"""
        from apps.video_ao_vivo.models import CountingSession
        
        # Obter caminho do modelo e converter para relativo
        model_path, model_config = self._get_model_path_for_camera(camera)
        relative_model_path = self._get_relative_path(model_path)
        
        # Criar sessão no banco
        self.current_session = CountingSession.objects.create(
            user=user,
            camera=camera,
            model_used=relative_model_path
        )
        
        # Criar arquivo de log
        logs_dir = Path(settings.MEDIA_ROOT) / "counting_logs"
        logs_dir.mkdir(exist_ok=True)
        
        log_filename = f"session_{self.current_session.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.log_file = logs_dir / log_filename
        
        # Salvar apenas o caminho relativo ao MEDIA_ROOT
        relative_path = f"counting_logs/{log_filename}"
        self.current_session.log_file_path = relative_path
        self.current_session.save()
        
        # Inicializar arquivo de log
        log_data = {
            "session_id": self.current_session.id,
            "camera_id": camera.id,
            "camera_name": camera.name,
            "user_id": user.id,
            "started_at": datetime.now().isoformat(),
            "events": []
        }
        
        with open(self.log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
    
    def _end_session(self):
        """Finaliza sessão salvando totais"""
        if not self.current_session or not self.processor:
            return
        
        from django.utils import timezone
        
        # Atualizar sessão com totais finais
        self.current_session.ended_at = timezone.now()
        self.current_session.total_in = self.processor.counts.get("in", 0)
        self.current_session.total_out = self.processor.counts.get("out", 0)
        self.current_session.balance = self.current_session.total_in - self.current_session.total_out
        self.current_session.save()
        
        # Finalizar log
        if self.log_file and self.log_file.exists():
            try:
                with open(self.log_file, 'r') as f:
                    log_data = json.load(f)
                
                log_data["ended_at"] = timezone.now().isoformat()
                log_data["total_in"] = self.current_session.total_in
                log_data["total_out"] = self.current_session.total_out
                log_data["balance"] = self.current_session.balance
                
                with open(self.log_file, 'w') as f:
                    json.dump(log_data, f, indent=2)
            except Exception as e:
                print(f"Erro ao finalizar log: {e}")
        
        self.current_session = None
        self.log_file = None

    def status(self):
        with self.lock:
            if not self.processor:
                return {"running": False, "paused": False, "in": 0, "out": 0}

            return {
                "running": self.processor.is_running,
                "paused": self.processor.is_paused,
                "in": int(self.processor.counts.get("in", 0)),
                "out": int(self.processor.counts.get("out", 0)),
            }


    def set_line_y_norm(self, y_norm: float):
        with self.lock:
            # Salvar a posição para preservar entre reinicializações
            self._saved_line_y_norm = max(0.0, min(1.0, float(y_norm)))
            if self.processor:
                self.processor.set_line_y_norm(self._saved_line_y_norm)

    def get_latest_jpeg(self):
        with self.lock:
            return self.processor.latest_jpeg if self.processor else None
    
    def _log_event(self, event):
        """Salva evento no arquivo de log"""
        if not self.log_file or not self.log_file.exists():
            return
        
        try:
            with open(self.log_file, 'r') as f:
                log_data = json.load(f)
            
            log_data["events"].append({
                "timestamp": datetime.fromtimestamp(event["ts"]).isoformat(),
                "kind": event["kind"],
                "track_id": event["track_id"],
                "delta": event["delta"]
            })
            
            with open(self.log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
                
        except Exception as e:
            print(f"Erro ao salvar evento no log: {e}")
    
    def _get_relative_path(self, absolute_path):
        """Converte caminho absoluto para relativo"""
        try:
            abs_path = Path(absolute_path)
            
            # Se está dentro do MEDIA_ROOT, fazer relativo a ele
            media_root = Path(settings.MEDIA_ROOT)
            if str(abs_path).startswith(str(media_root)):
                return str(abs_path.relative_to(media_root))
            
            # Se está dentro do BASE_DIR, fazer relativo a ele
            base_dir = Path(settings.BASE_DIR)
            if str(abs_path).startswith(str(base_dir)):
                return str(abs_path.relative_to(base_dir))
            
            # Fallback: apenas o nome do arquivo
            return abs_path.name
            
        except (ValueError, AttributeError):
            # Se não conseguir converter, retorna apenas o nome do arquivo
            return Path(absolute_path).name

counter_manager = CounterManager()
