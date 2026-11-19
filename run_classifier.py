"""
run_classifier.py — Week 1 issue-classification runner (dynamic multi-prompt version).

Layout — follows the STARTER PATH on slide 23 of Slide Package V12:
    data/issues.jsonl    -> the kit equivalent is read directly:
                            data/evaluation/issue_classification_gold.json
                            (only the `text` field is used as input; the labels
                            in that file are the answer key and are never sent)
    prompts/v1.md        -> one file per prompt version: v1.md, v2.md, v3.md...
                            The file's whole text IS the system prompt, word for word.
    run_eval.py          -> this file (run) + scripts/evaluate_issue_classifier.py (score)
    reports/results.csv  -> reports/results_v1.csv, results_v2.csv, ...
                            (one separate results file per prompt version)

How it works:
  1. Reads the API key + model name from the .env file (the key is NEVER written in code).
  2. Finds every prompts/*.md file — or just one version if you pass its name.
  3. For each prompt: sends the 20 case texts to the model with that prompt,
     validates every reply with Pydantic, writes reports/results_<version>.csv.
  4. A prompt file whose text starts with TODO is skipped (a placeholder for a
     version that is not written yet) — unfinished versions cost no API calls.

Run (from the kit folder, with the venv activated):
    python run_classifier.py        -> run every finished prompt in prompts/
    python run_classifier.py v2     -> run only prompts/v2.md
Score a result file (the scorer accepts any path):
    python scripts/evaluate_issue_classifier.py reports/results_v2.csv

Slide 23 implementation path, in this file:
  1. Create the answer key first -> provided by the kit (the gold file above);
     human-defined labels, never edit that file.
  2. Version the prompts -> separate files in prompts/, one version per file.
  3. Validate every response -> the Classification model below; invalid JSON is
     recorded as INVALID, i.e. counted as a failure.
  4. Compare on the same 20 cases -> the same input file for every version;
     one results CSV per version, all scored with the same scorer.

Learning note: read and understand every part. The mentor will ask why each
prompt version is written the way it is and what changed between versions.
"""

import csv
import json
import os
import sys
from pathlib import Path
from typing import Literal

try:
    from dotenv import load_dotenv
    from openai import OpenAI
    from pydantic import BaseModel, ValidationError
except ImportError:
    # If the requirements are not installed yet (or the venv is not active),
    # do not dump a confusing traceback — report the missing step clearly and stop.
    print("CANNOT RUN: required libraries are missing (python-dotenv/openai/pydantic).")
    print("In PowerShell, from the kit folder, activate the venv and run:")
    print("  .venv\\Scripts\\Activate.ps1")
    print("  pip install -r requirements.txt")
    print("Then run again: python run_classifier.py")
    sys.exit(1)

# ---------------------------------------------------------------- output structure
# Slide step 3 "Validate every response": parse the model output into typed
# fields; invalid JSON is marked as a failure (the INVALID rows below).
class Classification(BaseModel):
    category: Literal["Bug", "Feature", "Question", "Risk"]
    priority: Literal["P1", "P2", "P3"]
    next_action: str


def find_prompts(prompts_dir: Path, only: str | None) -> list[tuple[str, str]]:
    """Return [(version_name, prompt_text)] for every finished prompt file.

    Dynamic: any *.md file dropped into prompts/ is picked up automatically.
    Files whose text starts with TODO are placeholders and are skipped.
    `only` (e.g. "v2") restricts the run to that single version.
    """
    if not prompts_dir.is_dir():
        print(f"CANNOT RUN: no prompts folder found at {prompts_dir}")
        print("Create the prompts folder next to this script and put v1.md, v2.md, ... in it.")
        sys.exit(1)

    found = []
    for path in sorted(prompts_dir.glob("*.md")):
        version = path.stem.lower()  # "v1.md" -> "v1"
        if only and version != only:
            continue
        text = path.read_text(encoding="utf-8").strip()
        if not text or text.startswith("TODO"):
            print(f"{version}: skipped (placeholder, not written yet)")
            continue
        found.append((version, text))

    if not found:
        if only:
            print(f"CANNOT RUN: no finished prompt named '{only}' in {prompts_dir}")
        else:
            print("CANNOT RUN: no finished prompt files in the prompts folder.")
        sys.exit(1)
    return found


def run_version(version: str, prompt: str, cases: list, client: OpenAI, model: str) -> list:
    """Run one prompt version over all cases; return the CSV rows."""
    print(f"\n===== {version} =====")
    rows = []
    for case in cases:
        # Send only the text field to the model — never the answer key
        response = client.chat.completions.create(
            model=model,
            temperature=0,  # fixed so repeated runs are reproducible
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": case["text"]},
            ],
        )
        raw = response.choices[0].message.content or ""
        try:
            result = Classification.model_validate_json(raw)
            rows.append((case["issue_id"], result.category, result.priority))
            print(f'{case["issue_id"]}: {result.category}/{result.priority}')
        except ValidationError:
            # Malformed model reply -> record INVALID so the scorer counts it as wrong,
            # and print it so the schema failure is visible instead of hidden
            rows.append((case["issue_id"], "INVALID", "INVALID"))
            print(f'{case["issue_id"]}: INVALID FORMAT -> {raw[:80]}')
    return rows


def main() -> None:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY", "")
    model = os.getenv("OPENAI_MODEL", "")

    # No key yet, or the model is still the placeholder -> stop and say so, never fabricate results
    if not api_key or model in ("", "choose_approved_model"):
        print("CANNOT RUN: the .env file has no real OPENAI_API_KEY yet "
              "or OPENAI_MODEL is still 'choose_approved_model'.")
        print("Fill in the key + model provided by the AI Lead in .env, then run again.")
        sys.exit(1)

    kit_root = Path(__file__).parent
    # Slide step 1 "Create the answer key first": in this kit the answer key
    # already exists (human-defined by the organizers) — read-only, never edit.
    gold_path = kit_root / "data" / "evaluation" / "issue_classification_gold.json"
    cases = json.loads(gold_path.read_text(encoding="utf-8"))

    # Optional argument: run a single version, e.g. `python run_classifier.py v2`
    only = None
    if len(sys.argv) > 1:
        only = sys.argv[1].lower().removesuffix(".md")

    # Slide step 2 "Version the prompts": one file per version in prompts/.
    prompts = find_prompts(kit_root / "prompts", only)

    client = OpenAI(api_key=api_key)
    reports_dir = kit_root / "reports"
    reports_dir.mkdir(exist_ok=True)

    written = []
    for version, prompt in prompts:
        rows = run_version(version, prompt, cases, client, model)
        # Slide starter path: one separate results file per prompt version.
        out_path = reports_dir / f"results_{version}.csv"
        with out_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["issue_id", "predicted_category", "predicted_priority"])
            writer.writerows(rows)
        written.append(out_path)
        print(f"Wrote {len(rows)} rows to {out_path}")

    # Slide step 4 "Compare on the same 20 cases": score each version's file
    # with the same scorer and compare accuracy + P1 misses across versions.
    print("\nScore each version with:")
    for out_path in written:
        print(f"python scripts/evaluate_issue_classifier.py {out_path.relative_to(kit_root)}")


if __name__ == "__main__":
    main()
