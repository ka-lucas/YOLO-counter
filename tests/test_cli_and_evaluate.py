import pytest

from yolocounter.cli import build_parser
from yolocounter.evaluate import count_errors
from yolocounter.geometry import Line


def test_count_arguments():
    args = build_parser().parse_args(["count", "video.mp4", "--line", "0,300,1280,300", "--classes", "person", "car"])
    assert args.source == "video.mp4" and args.line == Line((0, 300), (1280, 300))
    assert args.classes == ["person", "car"] and args.tracker == "bytetrack.yaml"


def test_invalid_line_is_rejected():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["count", "v.mp4", "--line", "1,2,3"])


def test_count_errors():
    gt = {"a": {"in": 10, "out": 5}, "b": {"in": 0, "out": 4}}
    pred = {"a": {"in": 9, "out": 5}, "b": {"in": 1, "out": 4}}
    r = count_errors(pred, gt)
    assert r["mae_in"] == 1.0 and r["mae_out"] == 0.0
    assert r["mean_total_rel_err"] == pytest.approx((1 / 15 + 1 / 4) / 2)
    with pytest.raises(KeyError):
        count_errors({}, gt)
