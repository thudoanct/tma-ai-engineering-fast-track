"""FastAPI app for Week 2: POST /analyze-meeting.

Error mapping (study guide, Week 2 error table):
- invalid payload / empty notes -> 422 (FastAPI/Pydantic, automatic)
- OpenAI timeout after bounded retry -> 504 {"error": "upstream_timeout"}
- OpenAI 429 after bounded retry -> 503 {"error": "upstream_rate_limited"}
- upstream 5xx -> 502 {"error": "upstream_error"}
- model output fails Pydantic validation -> 502
  {"error": "invalid_upstream_response"}
Never a stack trace, never the API key, never the raw payload in an
error body.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app import schemas
from app.services import llm

app = FastAPI(title="Week 2 — Meeting Notes API")


def _error_response(status: int, code: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": code})


@app.exception_handler(llm.UpstreamTimeout)
async def _timeout_handler(request: Request, exc: llm.UpstreamTimeout) -> JSONResponse:
    return _error_response(504, "upstream_timeout")


@app.exception_handler(llm.UpstreamRateLimited)
async def _rate_limit_handler(
    request: Request, exc: llm.UpstreamRateLimited
) -> JSONResponse:
    return _error_response(503, "upstream_rate_limited")


@app.exception_handler(llm.InvalidUpstreamResponse)
async def _invalid_output_handler(
    request: Request, exc: llm.InvalidUpstreamResponse
) -> JSONResponse:
    return _error_response(502, "invalid_upstream_response")


@app.exception_handler(llm.UpstreamError)
async def _upstream_handler(request: Request, exc: llm.UpstreamError) -> JSONResponse:
    return _error_response(502, "upstream_error")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/analyze-meeting", response_model=schemas.MeetingAnalysis)
def analyze_meeting(payload: schemas.MeetingRequest) -> schemas.MeetingAnalysis:
    return llm.analyze_meeting(payload.meeting_text)
