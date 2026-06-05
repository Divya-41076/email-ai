import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import SCHEDULER_INTERVAL_MINUTES
from app.db.database import SessionLocal
from app.services.pipeline import run_pipeline

logger = logging.getLogger(__name__)

# Module-level singleton. AsyncIOScheduler integrates with FastAPI's running
# event loop (uvicorn), so start_scheduler() must be called from inside the
# loop — i.e. the lifespan startup (wired in Chunk 2), not at import time.
scheduler = AsyncIOScheduler(timezone="UTC")

JOB_ID = "email_pipeline"


def scheduled_run() -> None:
    """Job target invoked by APScheduler on each interval tick.

    Deliberately a *synchronous* function. run_pipeline() is blocking
    (sequential Gmail + Groq network calls, several seconds each). Under
    AsyncIOScheduler, a non-coroutine job is dispatched via
    loop.run_in_executor() — it runs on a worker thread and does NOT block
    the FastAPI event loop. Making this `async def` and awaiting nothing
    while calling the blocking pipeline would freeze the server instead.

    Each run gets its own short-lived DB session. Request-scoped sessions
    (from get_db) must never be reused here — they're tied to a request's
    lifecycle and would already be closed.
    """
    logger.info("[Scheduler] Triggered scheduled pipeline run")
    db = SessionLocal()
    try:
        result = run_pipeline(db)
        logger.info(
            f"[Scheduler] Run complete — processed: {result.get('processed', 0)}, "
            f"failed: {result.get('failed', 0)}"
        )
    except Exception as e:
        # A job that raises must not take down the scheduler or the app.
        # Log and swallow; the next tick will retry naturally.
        logger.error(f"[Scheduler] Pipeline run failed: {str(e)}")
    finally:
        db.close()


def start_scheduler() -> None:
    scheduler.add_job(
        scheduled_run,
        trigger="interval",
        minutes=SCHEDULER_INTERVAL_MINUTES,
        id=JOB_ID,
        replace_existing=True,   # idempotent if start is ever called twice
        max_instances=1,         # never overlap runs if one tick runs long
        coalesce=True,           # collapse missed ticks into a single run
        misfire_grace_time=60,   # tolerate up to 60s of scheduler delay
    )
    scheduler.start()
    logger.info(
        f"[Scheduler] Started — interval: {SCHEDULER_INTERVAL_MINUTES} min "
        f"(timezone: UTC,pinned)"
    )


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False) # dont wait for existing jobs running, just shutdown the scheduler and dont run anymore jobs
        logger.info("[Scheduler] Stopped")