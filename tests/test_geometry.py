import pytest

from yolocounter.geometry import Line


def test_parse_and_validation():
    line = Line.parse("0, 100, 640,100")
    assert line.start == (0.0, 100.0) and line.end == (640.0, 100.0)
    with pytest.raises(ValueError):
        Line.parse("1,2,3")
    with pytest.raises(ValueError):
        Line.parse("5,5,5,5")


def test_horizontal_line_crossing_directions():
    line = Line((0, 100), (200, 100))  # da esquerda para a direita
    # Em coordenadas de imagem (y para baixo), descer atravessa do lado positivo para o negativo
    down = line.crossed_by((50, 90), (50, 110))
    up = line.crossed_by((50, 110), (50, 90))
    assert down == -up and down != 0


def test_no_crossing_cases():
    line = Line((0, 100), (200, 100))
    assert line.crossed_by((50, 90), (60, 95)) == 0      # mesmo lado
    assert line.crossed_by((250, 90), (250, 110)) == 0   # cruza a reta fora do segmento
    assert line.crossed_by((50, 90), (50, 100)) == 0     # só toca a linha


def test_diagonal_line():
    line = Line((0, 0), (100, 100))
    assert line.crossed_by((60, 40), (40, 60)) != 0
    assert line.crossed_by((160, 140), (140, 160)) == 0
