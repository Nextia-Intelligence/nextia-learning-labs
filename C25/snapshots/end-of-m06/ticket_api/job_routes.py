"""The jobs of the queue: state, result, cancel, retry, and the queue's numbers (Module 4)."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from ticket_api import jobs
from ticket_api.db import Database
from ticket_api.intake import get_db
from ticket_api.models import ErrorResponse, Job, JobResult, QueueStats
from ticket_api.security import require_api_key

router = APIRouter(prefix="/v1", tags=["jobs"], dependencies=[Depends(require_api_key)])
JobId = Annotated[int, Path(ge=1)]
NOT_FOUND = {404: {"model": ErrorResponse, "description": "No such job."}}


def read_job(db: Database, job_id: int) -> Job:
    with db.connection() as conn:
        job = jobs.get(conn, job_id)
        if job is None:
            raise HTTPException(404, f"Job {job_id} does not exist.")
        result = None
        if job["state"] == "succeeded":
            row = conn.execute(
                "SELECT t.team, t.priority, t.needs_human,"
                " (SELECT output::json ->> 'reply' FROM ai_runs"
                "   WHERE job_id = %(id)s AND task = 'triage' AND status = 'ok') AS draft_reply,"
                " (SELECT embedding_version FROM ticket_embeddings e"
                "   WHERE e.ticket_id = t.ticket_id AND embedding_version = 'embed-small-384-v1')"
                "   AS embedding_version"
                " FROM tickets t WHERE t.ticket_id = %(ticket)s",
                {"id": job_id, "ticket": job["ticket_id"]},
            ).fetchone()
            result = JobResult(**row) if row else None
    return Job(**{k: job[k] for k in Job.model_fields if k in job}, result=result)


@router.get("/jobs/{job_id}", summary="Read a job: its state and result", responses=NOT_FOUND)
async def get_job(job_id: JobId, db: Annotated[Database, Depends(get_db)]) -> Job:
    return await run_in_threadpool(read_job, db, job_id)


@router.post(
    "/jobs/{job_id}/cancel",
    summary="Cancel a queued job",
    responses={409: {"model": ErrorResponse, "description": "The job is not queued."}, **NOT_FOUND},
)
async def cancel_job(job_id: JobId, db: Annotated[Database, Depends(get_db)]) -> Job:
    def cancel() -> None:
        with db.connection() as conn:
            job, changed = jobs.cancel(conn, job_id)
        if job is None:
            raise HTTPException(404, f"Job {job_id} does not exist.")
        if not changed:
            raise HTTPException(
                409, f"Job {job_id} is {job['state']}: only a queued job can be cancelled."
            )

    await run_in_threadpool(cancel)
    return await run_in_threadpool(read_job, db, job_id)


@router.post(
    "/jobs/{job_id}/retry",
    summary="Send a dead letter back to the queue",
    responses={
        409: {"model": ErrorResponse, "description": "The job is not a dead letter."},
        **NOT_FOUND,
    },
)
async def retry_job(job_id: JobId, db: Annotated[Database, Depends(get_db)]) -> Job:
    def retry() -> None:
        with db.connection() as conn:
            job, changed = jobs.requeue(conn, job_id)
        if job is None:
            raise HTTPException(404, f"Job {job_id} does not exist.")
        if not changed:
            raise HTTPException(409, f"Job {job_id} is {job['state']}, not a dead letter.")

    await run_in_threadpool(retry)
    return await run_in_threadpool(read_job, db, job_id)


@router.get("/queue", summary="The queue's numbers: waiting, running, oldest, finished")
async def queue_stats(request: Request, db: Annotated[Database, Depends(get_db)]) -> QueueStats:
    def read() -> dict:
        with db.connection() as conn:
            return jobs.stats(conn)

    return QueueStats(**await run_in_threadpool(read))


# ---------- what customers see (the MLOps course, Module 6) ----------

status_router = APIRouter(tags=["health"])
DELAYED_AFTER_SECONDS = 120  # the "drafts-late" alert's threshold


class ServiceStatus(BaseModel):
    status: Literal["ok", "delayed"]
    message: str = Field(description="The text that the website shows to customers.")
    queued: int
    oldest_waiting_seconds: float
    estimated_wait_seconds: float | None


def status_message(stats: dict) -> ServiceStatus:
    """Grace's wording: say what works, what is late, and what the customer should do."""
    oldest = stats["oldest_queued_seconds"]
    pace = stats["succeeded_last_minute"] / 60
    wait = round(stats["queued"] / pace, 1) if pace > 0 else None
    if oldest <= DELAYED_AFTER_SECONDS:
        return ServiceStatus(
            status="ok",
            message="We answer new tickets as usual.",
            queued=stats["queued"],
            oldest_waiting_seconds=oldest,
            estimated_wait_seconds=wait,
        )
    minutes = "a few" if wait is None else str(max(1, round(wait / 60)))
    return ServiceStatus(
        status="delayed",
        message=(
            "Your ticket is saved, and nothing is lost. Our replies take longer than usual "
            f"(about {minutes} minutes). You do not need to send your ticket again. If something "
            "is unsafe, stop using the product and call us."
        ),
        queued=stats["queued"],
        oldest_waiting_seconds=oldest,
        estimated_wait_seconds=wait,
    )


@status_router.get("/v1/status", summary="The service's status for customers (no API key)")
async def service_status(db: Annotated[Database, Depends(get_db)]) -> ServiceStatus:
    def read() -> dict:
        with db.connection() as conn:
            return jobs.stats(conn)

    return status_message(await run_in_threadpool(read))
