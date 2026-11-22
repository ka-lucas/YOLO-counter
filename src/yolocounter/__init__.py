"""YOLO Counter: contagem de objetos em vídeo por cruzamento de linha, com detecção YOLO e rastreamento."""

from .counter import CountEvent, LineCounter
from .geometry import Line

__all__ = ["CountEvent", "Line", "LineCounter"]
__version__ = "0.1.0"
