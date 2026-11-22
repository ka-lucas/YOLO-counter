import pytest

from yolocounter import Line, LineCounter


def box_at(x, y, w=20, h=40):
    """Caixa cujo centro da base está em (x, y)."""
    return (x - w / 2, y - h, x + w / 2, y)


def run(counter, trajectories, label="person"):
    """trajectories: {track_id: [(x, y), ...]} com uma posição por quadro."""
    n = max(len(t) for t in trajectories.values())
    for frame in range(n):
        tracks = [(tid, box_at(*pts[frame]), label) for tid, pts in trajectories.items() if frame < len(pts)]
        counter.update(frame, tracks, timestamp_s=frame / 30)
    return counter.totals()


def test_counts_each_direction():
    c = LineCounter(Line((0, 100), (300, 100)))
    totals = run(c, {
        1: [(50, 60), (50, 90), (50, 120), (50, 150)],   # desce
        2: [(150, 150), (150, 105), (150, 80)],          # sobe
        3: [(250, 40), (250, 60), (250, 80)],            # não cruza
    })
    assert totals["total"] == 2 and totals["in"] == 1 and totals["out"] == 1
    directions = {e.track_id: e.direction for e in c.events}
    assert directions[1] != directions[2]


def test_jitter_on_line_counts_once_per_direction():
    c = LineCounter(Line((0, 100), (300, 100)))
    totals = run(c, {7: [(50, 95), (50, 105), (50, 95), (50, 105), (50, 95)]})
    assert totals["total"] == 2  # uma vez em cada sentido


def test_point_exactly_on_line_is_not_lost():
    c = LineCounter(Line((0, 100), (300, 100)))
    totals = run(c, {1: [(50, 90), (50, 100), (50, 100), (50, 110)]})
    assert totals["total"] == 1


def test_by_class_and_event_fields():
    c = LineCounter(Line((0, 100), (300, 100)))
    c.update(0, [(1, box_at(10, 90), "car"), (2, box_at(30, 90), "person")])
    events = c.update(1, [(1, box_at(10, 110), "car"), (2, box_at(30, 110), "person")], timestamp_s=0.5)
    assert len(events) == 2 and events[0].frame == 1 and events[0].timestamp_s == 0.5
    by_class = c.totals()["by_class"]
    assert sum(by_class["car"].values()) == 1 and sum(by_class["person"].values()) == 1


def test_center_anchor_and_reset():
    c = LineCounter(Line((0, 100), (300, 100)), anchor="center")
    # base cruza, mas o centro (20 px acima) não
    run(c, {1: [(50, 95), (50, 115)]})
    assert c.totals()["total"] == 0
    c.reset()
    assert c.events == [] and c.totals()["total"] == 0
    with pytest.raises(ValueError):
        LineCounter(Line((0, 0), (1, 1)), anchor="top")
