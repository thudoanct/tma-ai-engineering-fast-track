"""Pydantic schemas for the Week 2 meeting-notes API.

Contract — aligned on 2026-11-27 to the mentor's shared evaluation
dataset (week2_meeting_notes_expected_20_cases, distributed to all 8
cohort members):
- Request: ``{"meeting_text": "..."}``. Empty / whitespace-only text
  is rejected with 422 before any LLM call is made.
- Response: ``{"summary": str, "decisions": list[str],
  "actions": [{"owner": str|null, "action": str,
  "due_date": "YYYY-MM-DD"|null}]}``.
- The "no invention" rule lives in the schema itself: ``owner`` and
  ``due_date`` are optional and default to ``None``. If the notes do
  not assign an owner or state a concrete date, the model must return
  null rather than guessing.
- Dates: a stated calendar date is returned as ISO; when the year is
  not written it is resolved from the meeting date in the notes.
  Vague timing with no concrete date ("sometime", "when ready")
  stays null.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, field_validator


class MeetingRequest(BaseModel):
    meeting_text: str = Field(
        ...,
        description="Full text of the meeting notes to analyse.",
    )

    @field_validator("meeting_text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("meeting_text must not be empty")
        return value


class ActionItem(BaseModel):
    owner: str | None = Field(
        default=None,
        description="Who must do it. Null when the notes assign nobody.",
    )
    action: str = Field(..., description="What needs to be done.")
    due_date: date | None = Field(
        default=None,
        description=(
            "ISO date (YYYY-MM-DD) when the notes state a concrete "
            "calendar date (year resolved from the meeting date when "
            "not written). Null when no concrete date is stated."
        ),
    )


class MeetingAnalysis(BaseModel):
    summary: str = Field(..., description="Short summary of the meeting.")
    decisions: list[str] = Field(
        default_factory=list,
        description="Decisions made in the meeting; empty when none were made.",
    )
    actions: list[ActionItem] = Field(
        default_factory=list,
        description="Action items; empty when nothing was assigned.",
    )
