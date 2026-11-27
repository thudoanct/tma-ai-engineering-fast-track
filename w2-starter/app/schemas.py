"""Pydantic schemas for the Week 2 meeting-notes API.

Contract (slides 24-25, Gate 1):
- Request: the raw meeting notes. Empty / whitespace-only notes are
  rejected with 422 before any LLM call is made.
- Response: summary + decisions + action items.
- The "no invention" rule lives in the schema itself: ``owner`` and
  ``due_date`` are optional and default to ``None``. If the notes do
  not name an owner or a concrete date, the model must return null
  rather than guessing a name or converting a relative date
  ("next Friday", "tomorrow") into an ISO date.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, field_validator


class MeetingRequest(BaseModel):
    meeting_notes: str = Field(
        ...,
        description="Full text of the meeting notes to analyse.",
    )
    meeting_id: str | None = Field(
        default=None,
        description="Optional meeting id, echoed nowhere in the analysis.",
    )

    @field_validator("meeting_notes")
    @classmethod
    def notes_must_not_be_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("meeting_notes must not be empty")
        return value


class ActionItem(BaseModel):
    task: str = Field(..., description="What needs to be done.")
    owner: str | None = Field(
        default=None,
        description="Who must do it. Null when the notes assign nobody.",
    )
    due_date: date | None = Field(
        default=None,
        description=(
            "ISO date (YYYY-MM-DD) only when the notes state an explicit "
            "date. Null for relative dates such as 'next Friday'."
        ),
    )


class MeetingAnalysis(BaseModel):
    summary: str = Field(..., description="Short summary of the meeting.")
    decisions: list[str] = Field(
        default_factory=list,
        description="Decisions made in the meeting; empty when none were made.",
    )
    action_items: list[ActionItem] = Field(
        default_factory=list,
        description="Action items; empty when nothing was assigned.",
    )
