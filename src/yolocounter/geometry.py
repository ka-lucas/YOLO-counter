"""Geometria 2D usada pela contagem: linha virtual e teste de cruzamento de segmentos."""
from __future__ import annotations

from dataclasses import dataclass

Point = tuple[float, float]


def _cross(o: Point, a: Point, b: Point) -> float:
    """Produto vetorial (a - o) x (b - o). Positivo: b à esquerda de o→a; negativo: à direita."""
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


@dataclass(frozen=True)
class Line:
    """Linha de contagem definida por dois pontos, em pixels."""

    start: Point
    end: Point

    @classmethod
    def parse(cls, text: str) -> "Line":
        """Lê "x1,y1,x2,y2"."""
        values = [float(v) for v in text.replace(" ", "").split(",")]
        if len(values) != 4:
            raise ValueError(f'linha deve ter 4 números "x1,y1,x2,y2", recebido: {text!r}')
        x1, y1, x2, y2 = values
        if (x1, y1) == (x2, y2):
            raise ValueError("os dois pontos da linha não podem ser iguais")
        return cls((x1, y1), (x2, y2))

    @classmethod
    def horizontal(cls, width: int, height: int, ratio: float = 0.5) -> "Line":
        """Linha horizontal atravessando o quadro inteiro, na altura ratio * altura."""
        y = height * ratio
        return cls((0.0, y), (float(width), y))

    def side(self, p: Point) -> float:
        """Sinal indica o lado do ponto em relação à linha (0 = sobre a linha)."""
        return _cross(self.start, self.end, p)

    def crossed_by(self, p: Point, q: Point) -> int:
        """Retorna +1 se o movimento p→q cruzou a linha da esquerda para a direita (lado positivo
        para o negativo), -1 no sentido contrário e 0 se não cruzou o segmento da linha.

        Tocar a linha sem atravessar não conta: o movimento precisa sair de um lado e chegar
        estritamente ao outro.
        """
        sp, sq = self.side(p), self.side(q)
        if sp == 0 or sq == 0 or (sp > 0) == (sq > 0):
            return 0
        # O movimento troca de lado da reta; confere se cruza dentro do segmento da linha.
        d1, d2 = _cross(p, q, self.start), _cross(p, q, self.end)
        if (d1 > 0) == (d2 > 0) and d1 != 0 and d2 != 0:
            return 0
        return 1 if sp > 0 else -1
