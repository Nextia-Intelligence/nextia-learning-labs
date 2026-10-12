"""Agents' reviews: the labels that arrive later (the MLOps course, Module 4).

    POST /v1/tickets/{ticket_id}/review  {"team": "delivery", "needs_human": true,
                                          "reviewed_by": "agent-07"}

When an agent has handled a ticket, the help desk's tool sends what was right: the team, and
whether a person had to handle it. The API saves it next to the assistant's decision and logs
a ticket.reviewed event (with the delay since the ticket arrived). These reviews are the true
labels of the assistant's work: they arrive hours or days after the decision, and only for
the tickets that agents handle.
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, ConfigDict, Field

from ticket_api import repository, telemetry
from ticket_api.db import Database
from ticket_api.intake import get_db
from ticket_api.models import ErrorResponse, Team
from ticket_api.security import require_api_key

router = APIRouter(prefix="/v1/tickets", tags=["tickets"], dependencies=[Depends(require_api_key)])


class ReviewIn(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [{"team": "delivery", "needs_human": True, "reviewed_by": "agent-07"}]
        },
    )
    team: Team
    needs_human: bool
    reviewed_by: str = Field(min_length=1, max_length=40, pattern=r"^[a-z0-9-]+$")


class Review(BaseModel):
    ticket_id: str
    team: Team
    needs_human: bool
    assistant_team: str | None = Field(description="None if the assistant gave no valid answer.")
    assistant_needs_human: bool | None
    agrees: bool = Field(description="The assistant's team and needs_human were both right.")
    prompt_version: str | None
    release_id: str | None
    delay_seconds: float = Field(description="From the ticket's arrival to this review.")


def agrees(row: dict) -> bool:
    return (
        row["assistant_team"] == row["team"] and row["assistant_needs_human"] is row["needs_human"]
    )


@router.post(
    "/{ticket_id}/review",
    summary="Record an agent's review of the assistant's decision (a delayed label)",
    responses={404: {"model": ErrorResponse, "description": "No such ticket."}},
)
async def review_ticket(
    review: ReviewIn,
    db: Annotated[Database, Depends(get_db)],
    ticket_id: Annotated[str, Path(pattern=r"^T-[0-9]{5,7}$")],
) -> Review:
    def save() -> dict | None:
        with db.connection() as conn:
            return repository.save_review(
                conn, ticket_id, review.team, review.needs_human, review.reviewed_by
            )

    row = await run_in_threadpool(save)
    if row is None:
        raise HTTPException(404, f"Ticket {ticket_id} does not exist.")
    delay = (datetime.now(UTC) - row["created_at"]).total_seconds()
    result = Review(
        **{k: row[k] for k in Review.model_fields if k in row},
        agrees=agrees(row),
        delay_seconds=round(delay, 1),
    )
    telemetry.event(
        "ticket.reviewed",
        {
            "ticket.id": ticket_id,
            "label.team": review.team,
            "label.needs_human": review.needs_human,
            "assistant.team": row["assistant_team"],
            "assistant.needs_human": row["assistant_needs_human"],
            "agrees": result.agrees,
            "review.delay_s": result.delay_seconds,
            "prompt.version": row["prompt_version"],
            "release.id": row["release_id"],
        },
    )
    telemetry.zero_series(row["prompt_version"] or "none", row["release_id"] or "none")
    telemetry.instruments().reviewed.add(
        1,
        {
            "agrees": str(result.agrees).lower(),
            "prompt.version": row["prompt_version"] or "none",
            "release.id": row["release_id"] or "none",
            "label.needs_human": str(review.needs_human).lower(),
        },
    )
    return result
