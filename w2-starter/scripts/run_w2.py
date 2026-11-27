"""Run the Week 2 endpoint over the 20 practice cases and save results.

Usage (from the w2-starter folder, venv active, .env with a real key):
    python scripts\\run_w2.py

This calls POST /analyze-meeting in-process (FastAPI TestClient), so
it exercises the real endpoint — validation, prompt, LLM call and
error mapping — without needing a second terminal for uvicorn.
Results go to reports\\w2_results.json; score them with:
    python scripts\\evaluate_w2.py

The practice cases are NOT gold: see ../w2-practice-cases-README.md.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

CASES_PATH = ROOT.parent / "w2-practice-cases.json"
if not CASES_PATH.exists():
    # Thu may have copied this folder on its own: the cases file can
    # also sit directly inside w2-starter/.
    CASES_PATH = ROOT / "w2-practice-cases.json"
if not CASES_PATH.exists():
    raise SystemExit(
        "Cannot find w2-practice-cases.json — copy it into this folder "
        "or next to it, then run again."
    )
OUT_PATH = ROOT / "reports" / "w2_results.json"


def main() -> None:
    data = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    client = TestClient(app, raise_server_exceptions=False)
    results = []
    for case in data["cases"]:
        resp = client.post(
            "/analyze-meeting", json={"meeting_notes": case["notes"]}
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
