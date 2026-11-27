"""Score Week 2 results against the 20 practice cases.

Usage (from the w2-starter folder):
    python scripts\\evaluate_w2.py [reports\\w2_results.json]

Scoring — exactly as in ../w2-practice-cases-README.md (52 facts):
- each expected decision = 1 point, counted when a predicted
  decision matches it in meaning (normalised text containment);
- each expected action item = 1 point, counted only when the task
  matches in meaning AND owner AND due_date are both exactly right,
  including null;
- W2P-12 (discussion only, nothing decided) = 1 discipline point
  when both predicted lists are empty.
- summary is NOT scored here; check it by eye against
  expected_summary_points in the cases file.

Pass bar (mirrors Gate 1, >=85%): >= 45/52.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES_PATH = ROOT.parent / "w2-practice-cases.json"
if not CASES_PATH.exists():
    CASES_PATH = ROOT / "w2-practice-cases.json"
if not CASES_PATH.exists():
    raise SystemExit(
        "Cannot find w2-practice-cases.json — copy it into this folder "
        "or next to it, then run again."
    )
PASS_MARK = 45
TOTAL_FACTS = 52


def norm(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def text_matches(expected: str, predicted: str) -> bool:
    a, b = norm(expected), norm(predicted)
    if not a or not b:
        return False
    return a == b or a in b or b in a


def owner_matches(expected, predicted) -> bool:
    if expected is None and predicted is None:
        return True
    if expected is None or predicted is None:
        return False
    return norm(str(expected)) == norm(str(predicted))


def score_case(case: dict, predicted: dict | None) -> tuple[int, int, list[str]]:
    """Return (points, facts, misses) for one case."""
    misses: list[str] = []
    if predicted is None:
        facts = (
            len(case.get("expected_decisions", []))
            + len(case.get("expected_action_items", []))
            + (1 if case["id"] == "W2P-12" else 0)
        )
        return 0, facts, ["no usable response (endpoint error)"]
    points = 0
    facts = 0
    pred_decisions = predicted.get("decisions") or []
    for expected in case.get("expected_decisions", []):
        facts += 1
        if any(text_matches(expected, p) for p in pred_decisions):
            points += 1
        else:
            misses.append(f"decision missed: {expected}")
    pred_actions = predicted.get("action_items") or []
    for expected in case.get("expected_action_items", []):
        facts += 1
        hit = False
        for pred in pred_actions:
            if (
                text_matches(expected["task"], pred.get("task", ""))
                and owner_matches(expected.get("owner"), pred.get("owner"))
                and (expected.get("due_date") or None)
                == (pred.get("due_date") or None)
            ):
                hit = True
                break
        if hit:
            points += 1
        else:
            misses.append(
                "action missed: "
                f"{expected['task']} (owner={expected.get('owner')}, "
                f"due={expected.get('due_date')})"
            )
    if case["id"] == "W2P-12":
        facts += 1
        if not pred_decisions and not pred_actions:
            points += 1
        else:
            misses.append("W2P-12: lists should both be empty")
    return points, facts, misses


def main() -> None:
    results_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "reports" / "w2_results.json"
    cases = {c["id"]: c for c in json.loads(CASES_PATH.read_text(encoding="utf-8"))["cases"]}
    results = json.loads(results_path.read_text(encoding="utf-8"))
    total_points = 0
    total_facts = 0
    for entry in results:
        case = cases[entry["id"]]
        points, facts, misses = score_case(case, entry.get("predicted"))
        total_points += points
        total_facts += facts
        flag = "OK " if not misses else "MISS"
        print(f"{entry['id']}: {points}/{facts} {flag}")
        for miss in misses:
            print(f"    - {miss}")
    print(f"\nTotal: {total_points}/{total_facts} facts")
    print(f"Pass mark (>=85%): {PASS_MARK}/{TOTAL_FACTS}")
    print("PASS" if total_points >= PASS_MARK else "NOT YET — see misses above")


if __name__ == "__main__":
    main()
