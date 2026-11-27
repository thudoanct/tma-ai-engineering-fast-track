"""Score Week 2 results against the mentor's official 20 cases.

Usage (from the w2-starter folder):
    python scripts\\evaluate_official.py [reports\\w2_official_results.json]

Scoring follows the mentor's suggested evaluation process
(week2_meeting_notes_expected_20_cases.md):
- fact-level scoring: each expected decision = 1 fact, each expected
  action = 1 fact; total facts in the official set: 52
  (15 decisions + 37 actions);
- the mentor's contract says decisions and action descriptions are
  compared SEMANTICALLY — "surface wording differences should not
  automatically fail an otherwise equivalent fact" — while owner and
  due_date are checked strictly (exact match, including null).
  This scorer approximates the semantic comparison deterministically:
  dates are normalised to one form ("December 7, 2026" and
  "2026-12-07" become the same token), filler words are dropped,
  word endings are stemmed, and two texts match when one contains
  the other or their word overlap (Dice) is >= 0.70.
  (Revision note, 2026-11-27: the first version of this scorer used
  plain text containment, which failed correct answers over a single
  inserted word such as "the" or "some" — stricter than the mentor's
  own contract. The threshold version above replaces it.)
- predicted decisions/actions that match nothing expected are counted
  separately as "invented" (the precision side) and also disqualify a
  case from being "fully passing";
- a case is fully passing when it scores all its facts with no
  invented output (empty cases pass only when both lists come back
  empty);
- summary is NOT scored; check it by eye.

Pass bar mirrors slide 24 (>=85% fact extraction): >= 45/52.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES_PATH = ROOT / "week2_meeting_notes_expected_20_cases.json"
PASS_MARK = 45
TOTAL_FACTS = 52
MATCH_THRESHOLD = 0.70

MONTHS = {
    "january": "01", "february": "02", "march": "03", "april": "04",
    "may": "05", "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
}

STOPWORDS = {
    "the", "a", "an", "to", "of", "for", "on", "in", "by", "and",
    "or", "with", "from", "that", "this", "it", "is", "are", "was",
    "were", "be", "been", "as", "at",
}


def _date_token(year: str, month: str, day: str) -> str:
    return f"d{year}{month}{int(day):02d}"


def normalize_dates(text: str) -> str:
    """Rewrite every date expression to one canonical token."""
    text = re.sub(
        r"\b(\d{4})-(\d{2})-(\d{2})\b",
        lambda m: " " + _date_token(m.group(1), m.group(2), m.group(3)) + " ",
        text,
    )
    # Shared-year range: "December 3 to December 7, 2026" — the year is
    # written once at the end but belongs to both dates.
    text = re.sub(
        r"\b(january|february|march|april|may|june|july|august|september|"
        r"october|november|december)\s+(\d{1,2})(?:st|nd|rd|th)?\s+(?:to|-)\s+"
        r"(january|february|march|april|may|june|july|august|september|"
        r"october|november|december)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b",
        lambda m: " "
        + _date_token(m.group(5), MONTHS[m.group(1)], m.group(2))
        + " "
        + _date_token(m.group(5), MONTHS[m.group(3)], m.group(4))
        + " ",
        text,
    )
    text = re.sub(
        r"\b(january|february|march|april|may|june|july|august|september|"
        r"october|november|december)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b",
        lambda m: " " + _date_token(m.group(3), MONTHS[m.group(1)], m.group(2)) + " ",
        text,
    )
    text = re.sub(
        r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(january|february|march|april|may|june|"
        r"july|august|september|october|november|december),?\s+(\d{4})\b",
        lambda m: " " + _date_token(m.group(3), MONTHS[m.group(2)], m.group(1)) + " ",
        text,
    )
    return text


def stem(word: str) -> str:
    if len(word) > 5 and word.endswith("ing"):
        word = word[:-3]
    elif len(word) > 4 and word.endswith("ed"):
        word = word[:-2]
    elif len(word) > 4 and word.endswith("es"):
        word = word[:-2]
    elif len(word) > 3 and word.endswith("s"):
        word = word[:-1]
    if len(word) > 3 and word.endswith("e"):
        word = word[:-1]
    return word


def tokens(text: str) -> set[str]:
    text = normalize_dates(text.lower())
    words = re.findall(r"[a-z0-9]+", text)
    return {stem(w) for w in words if w not in STOPWORDS}


def text_matches(expected: str, predicted: str) -> bool:
    a, b = tokens(expected), tokens(predicted)
    if not a or not b:
        return False
    if a <= b or b <= a:
        return True
    overlap = len(a & b)
    dice = 2 * overlap / (len(a) + len(b))
    return dice >= MATCH_THRESHOLD


def owner_matches(expected, predicted) -> bool:
    if expected is None and predicted is None:
        return True
    if expected is None or predicted is None:
        return False
    return str(expected).strip().lower() == str(predicted).strip().lower()


def score_case(case: dict, predicted: dict | None) -> tuple[int, int, list[str], int]:
    """Return (points, facts, misses, invented) for one case."""
    expected = case["expected"]
    exp_decisions = expected.get("decisions") or []
    exp_actions = expected.get("actions") or []
    facts = len(exp_decisions) + len(exp_actions)
    misses: list[str] = []
    if predicted is None:
        return 0, facts, ["no usable response (endpoint error)"], 0
    points = 0
    pred_decisions = predicted.get("decisions") or []
    for exp in exp_decisions:
        if any(text_matches(exp, p) for p in pred_decisions):
            points += 1
        else:
            misses.append(f"decision missed: {exp}")
    pred_actions = predicted.get("actions") or []
    for exp in exp_actions:
        hit = False
        for pred in pred_actions:
            if (
                text_matches(exp["action"], pred.get("action", ""))
                and owner_matches(exp.get("owner"), pred.get("owner"))
                and (exp.get("due_date") or None) == (pred.get("due_date") or None)
            ):
                hit = True
                break
        if hit:
            points += 1
        else:
            misses.append(
                "action missed: "
                f"{exp['action']} (owner={exp.get('owner')}, "
                f"due={exp.get('due_date')})"
            )
    invented = 0
    for pred in pred_decisions:
        if not any(text_matches(exp, pred) for exp in exp_decisions):
            invented += 1
            misses.append(f"decision invented: {pred}")
    for pred in pred_actions:
        if not any(
            text_matches(exp["action"], pred.get("action", ""))
            for exp in exp_actions
        ):
            invented += 1
            misses.append(
                "action invented: "
                f"{pred.get('action')} (owner={pred.get('owner')}, "
                f"due={pred.get('due_date')})"
            )
    return points, facts, misses, invented


def main() -> None:
    results_path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else ROOT / "reports" / "w2_official_results.json"
    )
    cases = {
        c["id"]: c
        for c in json.loads(CASES_PATH.read_text(encoding="utf-8"))
    }
    results = json.loads(results_path.read_text(encoding="utf-8"))
    total_points = 0
    total_facts = 0
    total_invented = 0
    fully_passing = 0
    for entry in results:
        case = cases[entry["id"]]
        points, facts, misses, invented = score_case(case, entry.get("predicted"))
        total_points += points
        total_facts += facts
        total_invented += invented
        full = points == facts and invented == 0 and entry.get("predicted") is not None
        if full:
            fully_passing += 1
        flag = "OK " if not misses else "MISS"
        print(f"{entry['id']}: {points}/{facts} {flag}")
        for miss in misses:
            print(f"    - {miss}")
    pct = (100.0 * total_points / total_facts) if total_facts else 0.0
    print(f"\nTotal: {total_points}/{total_facts} facts ({pct:.1f}%)")
    print(f"Fully passing cases: {fully_passing}/20")
    print(f"Invented facts (predicted, not in expected): {total_invented}")
    print(f"Pass mark (>=85%): {PASS_MARK}/{TOTAL_FACTS}")
    print("PASS" if total_points >= PASS_MARK else "NOT YET — see misses above")


if __name__ == "__main__":
    main()
