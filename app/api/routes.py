from fastapi import APIRouter, Depends, Request, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.db.database import get_db
from app.services.pipeline import run_pipeline
from app.models.email_model import Email, EmailAnalysis
import logging

from app.scheduler import scheduler, JOB_ID
from app.config import SCHEDULER_INTERVAL_MINUTES

logger = logging.getLogger(__name__)


limiter = Limiter(key_func=get_remote_address)
router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/process-emails")
@limiter.limit("10/minute")
def process_emails(request: Request, 
                   background_tasks:BackgroundTasks, 
                   db: Session = Depends(get_db)
                   ):
    try:

        background_tasks.add_task(run_pipeline, db)
        return {"status": "Processing",
                "message": "Emails queued for processing. Check /emails shortly."}
    except Exception as e:
        logger.error(f"[Routes] failed to queue pipeline: {str(e)}")
        raise HTTPException(status_code = 500, detail= "failed to start email processing")



@router.get("/emails")
def get_emails(db: Session = Depends(get_db)):
    try:

        emails = db.query(Email).all()
        results = []
        for email in emails:
            analysis = db.query(EmailAnalysis).filter(
                EmailAnalysis.email_id == email.id
            ).first()
            results.append({
                "id": email.id,
                "subject": email.subject,
                "sender": email.sender,
                "received_at": email.received_at,
                "analysis": {
                    "category": analysis.category if analysis else None,
                    "priority": analysis.priority if analysis else None,
                    "summary": analysis.summary if analysis else None,
                    "action_items": analysis.action_items if analysis else [],
                    "action": analysis.automation_action if analysis else None,
                    "status": analysis.status if analysis else None
                }
            })
        return results
    except SQLAlchemyError as e:
        logger.error(f"[Routes]DB error on get/emails: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while fetching the emails.")


@router.get("/emails/{email_id}")
def get_email(email_id: int, db: Session = Depends(get_db)):
    try:

        email = db.query(Email).filter(Email.id == email_id).first()
        if not email:
            return {"error": "Email not found"}
        analysis = db.query(EmailAnalysis).filter(
            EmailAnalysis.email_id == email_id
        ).first()
        return {
            "id": email.id,
            "subject": email.subject,
            "sender": email.sender,
            "received_at": email.received_at,
            "analysis": {
                "category": analysis.category if analysis else None,
                "priority": analysis.priority if analysis else None,
                "summary": analysis.summary if analysis else None,
                "action_items": analysis.action_items if analysis else [],
                "action": analysis.automation_action if analysis else None,
                "status": analysis.status if analysis else None
            }
        }
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"[Routes]DB error on get/emails/{email_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while fetching the email.")

@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    try:

        total_emails = db.query(Email).count()
        total_analysis = db.query(EmailAnalysis).count()
        actions = db.query(EmailAnalysis.automation_action).all()
        action_counts = {}
        for action in actions:
            a = action[0]
            action_counts[a] = action_counts.get(a, 0) + 1
        return {
            "emails_processed": total_emails,
            "actions_triggered": total_analysis,
            "action_breakdown": action_counts
        }
    except SQLAlchemyError as e:
        logger.error(f"[Routes]DB error on /stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while fetching stats.")

@router.get("/scheduler/status")
def scheduler_status():
    job = scheduler.get_job(JOB_ID)
    next_run = job.next_run_time.isoformat() if job and job.next_run_time else None
    return {
        "running": scheduler.running,
        "next_run": next_run,          # ISO 8601, UTC (APScheduler default tz)
        "interval_minutes": SCHEDULER_INTERVAL_MINUTES,
    }