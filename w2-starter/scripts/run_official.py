"""Run the Week 2 endpoint over the mentor's official 20 cases.

Usage (from the w2-starter folder, venv active, .env with a real key):
    python scripts\\run_official.py

Dataset: week2_meeting_notes_expected_20_cases.json in this folder —
the shared evaluation set the mentor distributed to all 8 members on
2026-11-21 (picked up and applied here on 2026-11-27). Each case's ``input`` is sent as ``meeting_text`` to
POST /analyze-meeting, exactly as the mentor's evaluation contract
prescribes. Calls go through FastAPI TestClient in-process, so the
real endpoint (validation, prompt, LLM call, error mapping) is
exercised without a second uvicorn terminal.
Results go to reports\\w2_official_results.json; score them with:
    python scripts\\evaluate_official.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

CASES_PATH = ROOT / "week2_meeting_notes_expected_20_cases.json"
OUT_PATH = ROOT / "reports" / "w2_official_results.json"


def main() -> None:
    if not CASES_PATH.exists():
        raise SystemExit(
            f"Cannot find {CASES_PATH.name} — it must sit in the "
            "w2-starter folder, next to this project's README."
        )
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    client = TestClient(app, raise_server_exceptions=False)
    results = []
    for case in cases:
        resp = client.post(
            "/analyze-meeting", json={"meeting_text": case["input"]}
        )
        entry = {"id": case["id"], "status": resp.status_code}
        if resp.status_code == 200:
            entry["predicted"] = resp.json()
        else:
            entry["predicted"] = None
            entry["error"] = resp.json()
        results.append(entry)
        print(f"{case['id']}: HTTP {resp.status_code}")
    OUT_PATH.parent.mkdir(exist_ok=True)
    OUT_PATH.write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Wrote {len(results)} results to {OUT_PATH}")


if __name__ == "__main__":
    main()
