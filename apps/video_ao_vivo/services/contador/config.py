from dataclasses import dataclass
from typing import Optional, Tuple

Point = Tuple[float, float]  # (x,y) normalizado 0..1

@dataclass
class CounterConfig:
    model_path: str
    conf_thres: float = 0.25
    resize_scale: float = 1.0
    device: str = "cpu"

    # linha normalizada (ponta a ponta = x=0 e x=1)
    line_y_norm: float = 0.5  # default no meio
    # se quiser suportar linha livre no futuro:
    line_p1: Optional[Point] = None
    line_p2: Optional[Point] = None
