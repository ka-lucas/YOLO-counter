"""Testa a API web sem rodar o YOLO (o pipeline é substituído por um falso)."""
import time

import numpy as np
import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from yolocounter import web  # noqa: E402
from yolocounter.counter import CountEvent  # noqa: E402
from yolocounter.pipeline import FrameResult  # noqa: E402


def fake_iter_count(cfg, stop=None, on_event=None):
    for i in range(3):
        events = [CountEvent(i, 1, "person", "in", i / 30)] if i == 1 else []
        totals = {"in": int(i >= 1), "out": 0, "total": int(i >= 1), "by_class": {}}
        yield FrameResult(i, i / 30, np.zeros((48, 64, 3), np.uint8), [], events, totals)


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(web, "iter_count", fake_iter_count)
    monkeypatch.setattr(web, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(web, "_job", None)
    return TestClient(web.app)


def wait_done(client):
    for _ in range(100):
        s = client.get("/api/jobs/current").json()
        if s["status"] in {"finished", "error", "stopped"}:
            return s
        time.sleep(0.02)
    raise AssertionError("contagem não terminou")


def test_index_and_idle(client):
    assert "YOLO Counter" in client.get("/").text
    assert client.get("/api/jobs/current").json() == {"status": "idle"}


def test_upload_flow(client):
    r = client.post("/api/jobs/upload", files={"file": ("v.mp4", b"fake", "video/mp4")},
                    data={"line": "0,10,64,10", "classes": "person"})
    assert r.status_code == 200
    s = wait_done(client)
    assert s["status"] == "finished" and s["totals"]["in"] == 1 and len(s["events"]) == 1


def test_rejects_bad_input(client):
    assert client.post("/api/jobs/upload", files={"file": ("v.txt", b"x", "text/plain")}).status_code == 415
    assert client.post("/api/jobs/stream", data={"source": "0", "line": "1,2"}).status_code == 422
