"""Pipeline de vídeo: detecção YOLO + rastreamento (ByteTrack/BoT-SORT) + contagem por linha."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Iterator

import cv2
import numpy as np

from .counter import CountEvent, LineCounter
from .draw import draw_frame
from .geometry import Line


@dataclass
class CountConfig:
    source: str | int
    model: str = "yolo11n.pt"
    line: Line | None = None          # None: linha horizontal no meio do quadro
    classes: list[str] | None = None  # None: todas as classes do modelo
    conf: float = 0.35
    imgsz: int = 640
    tracker: str = "bytetrack.yaml"
    anchor: str = "bottom"
    device: str | None = None         # "cpu", "0" (GPU), ou None para escolher automaticamente


@dataclass
class FrameResult:
    index: int
    timestamp_s: float | None
    image: np.ndarray                 # quadro anotado
    tracks: list
    new_events: list[CountEvent]
    totals: dict


@dataclass
class RunSummary:
    source: str
    model: str
    line: tuple
    frames: int
    fps_source: float | None
    processing_fps: float
    totals: dict
    events: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


def _class_ids(names: dict[int, str], wanted: list[str] | None) -> list[int] | None:
    if not wanted:
        return None
    lookup = {v.lower(): k for k, v in names.items()}
    missing = [w for w in wanted if w.lower() not in lookup]
    if missing:
        raise ValueError(f"classes não existem no modelo: {missing}. Exemplos: {list(names.values())[:10]}")
    return [lookup[w.lower()] for w in wanted]


def _open_source(source: str | int):
    src = int(source) if isinstance(source, str) and source.isdigit() else source
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        raise RuntimeError(f"não foi possível abrir a fonte de vídeo: {source}")
    return cap


def iter_count(cfg: CountConfig, stop: threading.Event | None = None,
               on_event: Callable[[CountEvent], None] | None = None) -> Iterator[FrameResult]:
    """Processa a fonte quadro a quadro e produz o quadro anotado com a contagem acumulada."""
    from ultralytics import YOLO  # import tardio: os testes do núcleo não precisam do PyTorch

    model = YOLO(cfg.model)
    class_ids = _class_ids(model.names, cfg.classes)
    cap = _open_source(cfg.source)
    fps = cap.get(cv2.CAP_PROP_FPS) or None
    counter: LineCounter | None = None
    index = 0
    try:
        while not (stop and stop.is_set()):
            ok, frame = cap.read()
            if not ok:
                break
            if counter is None:
                h, w = frame.shape[:2]
                counter = LineCounter(cfg.line or Line.horizontal(w, h), anchor=cfg.anchor)
            result = model.track(frame, persist=True, tracker=cfg.tracker, conf=cfg.conf, imgsz=cfg.imgsz,
                                 classes=class_ids, device=cfg.device, verbose=False)[0]
            tracks = []
            if result.boxes is not None and result.boxes.id is not None:
                for tid, box, cls in zip(result.boxes.id.int().tolist(), result.boxes.xyxy.tolist(),
                                         result.boxes.cls.int().tolist()):
                    tracks.append((tid, tuple(box), model.names[cls]))
            ts = index / fps if fps else None
            new_events = counter.update(index, tracks, timestamp_s=ts)
            if on_event:
                for e in new_events:
                    on_event(e)
            totals = counter.totals()
            image = draw_frame(frame, counter.line, tracks, totals, flash=bool(new_events))
            yield FrameResult(index, ts, image, tracks, new_events, totals)
            index += 1
    finally:
        cap.release()


def run_count(cfg: CountConfig, output_video: str | None = None, show: bool = False,
              progress: Callable[[FrameResult], None] | None = None) -> RunSummary:
    """Roda a contagem inteira e devolve o resumo. Opcionalmente grava o vídeo anotado."""
    writer = None
    events: list[CountEvent] = []
    last: FrameResult | None = None
    fps_source = None
    t0 = time.time()
    for r in iter_count(cfg, on_event=events.append):
        if writer is None and output_video:
            h, w = r.image.shape[:2]
            cap = _open_source(cfg.source)
            fps_source = cap.get(cv2.CAP_PROP_FPS) or 25.0
            cap.release()
            writer = cv2.VideoWriter(output_video, cv2.VideoWriter_fourcc(*"mp4v"), fps_source, (w, h))
        if writer is not None:
            writer.write(r.image)
        if show:
            cv2.imshow("YOLO Counter (q para sair)", r.image)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        if progress:
            progress(r)
        last = r
    elapsed = time.time() - t0
    if writer is not None:
        writer.release()
    if show:
        cv2.destroyAllWindows()
    frames = (last.index + 1) if last else 0
    line = cfg.line
    return RunSummary(
        source=str(cfg.source), model=cfg.model,
        line=(line.start, line.end) if line else ("horizontal", "meio do quadro"),
        frames=frames, fps_source=fps_source, processing_fps=round(frames / elapsed, 2) if elapsed else 0.0,
        totals=last.totals if last else {"in": 0, "out": 0, "total": 0, "by_class": {}},
        events=[e.to_dict() for e in events],
    )
