"""Contagem por cruzamento de linha a partir de objetos rastreados.

Cada objeto rastreado tem um identificador estável entre quadros. O contador guarda a última
posição de referência de cada identificador e registra um evento quando o deslocamento entre
dois quadros cruza a linha. Cada objeto é contado no máximo uma vez por sentido, o que evita
contagens repetidas quando ele oscila sobre a linha.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field

from .geometry import Line, Point

DIRECTION_NAMES = {1: "in", -1: "out"}


@dataclass(frozen=True)
class CountEvent:
    frame: int
    track_id: int
    label: str
    direction: str  # "in" ou "out"
    timestamp_s: float | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class LineCounter:
    """Conta objetos que cruzam uma linha.

    anchor: ponto da caixa usado como posição do objeto. "bottom" (centro da base) costuma ser
    melhor para pessoas e veículos vistos de cima ou de lado; "center" usa o centro da caixa.
    """

    line: Line
    anchor: str = "bottom"
    count_once: bool = True
    events: list[CountEvent] = field(default_factory=list)
    _last: dict[int, Point] = field(default_factory=dict, repr=False)
    _counted: set[tuple[int, int]] = field(default_factory=set, repr=False)

    def __post_init__(self) -> None:
        if self.anchor not in {"bottom", "center"}:
            raise ValueError('anchor deve ser "bottom" ou "center"')

    def anchor_point(self, box: tuple[float, float, float, float]) -> Point:
        x1, y1, x2, y2 = box
        cx = (x1 + x2) / 2
        return (cx, y2) if self.anchor == "bottom" else (cx, (y1 + y2) / 2)

    def update(self, frame: int, tracks: list[tuple[int, tuple[float, float, float, float], str]],
               timestamp_s: float | None = None) -> list[CountEvent]:
        """Processa os objetos rastreados de um quadro: lista de (id, caixa x1y1x2y2, rótulo).

        Retorna os eventos gerados neste quadro.
        """
        new_events = []
        for track_id, box, label in tracks:
            point = self.anchor_point(box)
            previous = self._last.get(track_id)
            if previous is not None:
                direction = self.line.crossed_by(previous, point)
                if direction and not (self.count_once and (track_id, direction) in self._counted):
                    self._counted.add((track_id, direction))
                    event = CountEvent(frame, track_id, label, DIRECTION_NAMES[direction], timestamp_s)
                    self.events.append(event)
                    new_events.append(event)
            # Pontos exatamente sobre a linha não viram referência, para não perder o cruzamento
            if self.line.side(point) != 0:
                self._last[track_id] = point
        return new_events

    def totals(self) -> dict:
        """Totais por sentido e por classe."""
        by_dir = Counter(e.direction for e in self.events)
        by_class: dict[str, dict[str, int]] = {}
        for e in self.events:
            by_class.setdefault(e.label, {"in": 0, "out": 0})[e.direction] += 1
        return {"in": by_dir["in"], "out": by_dir["out"], "total": len(self.events), "by_class": by_class}

    def reset(self) -> None:
        self.events.clear()
        self._last.clear()
        self._counted.clear()
