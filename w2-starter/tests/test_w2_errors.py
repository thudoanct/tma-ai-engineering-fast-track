"""The 5 mandatory Gate 1 error scenarios for POST /analyze-meeting.

Run (from the w2-starter folder, venv active):
    pytest -q tests\\test_w2_errors.py

No API key and no network are needed here: the LLM layer is mocked,
so these tests prove the endpoint's own behaviour — validation first,
then the error mapping from the study guide (422 / 504 / 503 / 502).

Contract updated 2026-11-27 to the mentor's shared evaluation
dataset: request field is ``meeting_text``; the response list is
``actions`` with items ``{"owner", "action", "due_date"}``.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from app.main import app
from app.schemas import MeetingAnalysis
from app.services import llm

client = TestClient(app, raise_server_exceptions=False)

GOOD_NOTES = (
    "Sprint planning, Project ALPHA, 23 Nov 2026. Team decided to move "
    "UAT to 30 Nov 2026 because staging is not ready. "
    "Lan will update the test plan by 27 Nov 2026."
)

GOOD_RESPONSE = {
    "summary": "Team moved UAT to 30 Nov 2026; Lan updates the test plan.",
    "decisions": ["Move UAT to 30 Nov 2026"],
    "actions": [
        {"owner": "Lan", "action": "Update the test plan", "due_date": "2026-11-27"}
    ],
}


def test_happy_path_returns_structured_output(monkeypatch):
    monkeypatch.setattr(
        llm, "analyze_meeting", lambda notes: MeetingAnalysis(**GOOD_RESPONSE)
    )
    resp = client.post("/analyze-meeting", json={"meeting_text": GOOD_NOTES})
    assert resp.status_code == 200
    assert resp.json()["decisions"] == ["Move UAT to 30 Nov 2026"]
    assert resp.json()["actions"][0]["owner"] == "Lan"


def test_invalid_payload_missing_notes():
    # 1/5 — payload khong hop le: thieu meeting_text -> 422, khong goi LLM
    resp = client.post("/analyze-meeting", json={})
    assert resp.status_code == 422


def test_empty_notes_rejected_before_llm_call(monkeypatch):
    # 1/5 (bien the) — bien ban rong -> 422 ngay, khong ton luot goi LLM
    called = []
    monkeypatch.setattr(llm, "analyze_meeting", lambda notes: called.append(notes))
    resp = client.post("/analyze-meeting", json={"meeting_text": "   "})
    assert resp.status_code == 422
    assert called == []


def test_timeout_maps_to_504(monkeypatch):
    # 2/5 — timeout sau retry -> 504
    monkeypatch.setattr(
        llm, "analyze_meeting", lambda notes: (_ for _ in ()).throw(llm.UpstreamTimeout("timed out"))
    )
    resp = client.post("/analyze-meeting", json={"meeting_text": GOOD_NOTES})
    assert resp.status_code == 504
    assert resp.json() == {"error": "upstream_timeout"}


def test_persistent_429_maps_to_503(monkeypatch):
    # 3/5 — 429 keo dai sau retry -> 503
    monkeypatch.setattr(
        llm, "analyze_meeting", lambda notes: (_ for _ in ()).throw(llm.UpstreamRateLimited("429"))
    )
    resp = client.post("/analyze-meeting", json={"meeting_text": GOOD_NOTES})
    assert resp.status_code == 503
    assert resp.json() == {"error": "upstream_rate_limited"}


def test_upstream_500_maps_to_502(monkeypatch):
    # 4/5 — upstream 500 -> 502
    monkeypatch.setattr(
        llm, "analyze_meeting", lambda notes: (_ for _ in ()).throw(llm.UpstreamError("500"))
    )
    resp = client.post("/analyze-meeting", json={"meeting_text": GOOD_NOTES})
    assert resp.status_code == 502
    assert resp.json() == {"error": "upstream_error"}


def test_invalid_model_output_maps_to_502(monkeypatch):
    # 5/5 — model tra output khong dung schema -> 502
    monkeypatch.setattr(
        llm,
        "analyze_meeting",
        lambda notes: (_ for _ in ()).throw(llm.InvalidUpstreamResponse("bad json")),
    )
    resp = client.post("/analyze-meeting", json={"meeting_text": GOOD_NOTES})
    assert resp.status_code == 502
    assert resp.json() == {"error": "invalid_upstream_response"}


def test_health():
    assert client.get("/health").json() == {"status": "ok"}
