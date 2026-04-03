import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.services.email_fetcher import fetch_emails
from app.services.ai_analyzer import analyze_email
from app.services.decision_engine import process_email_decision
from app.services.automation_service import execute_action
from app.models.email_model import Email, EmailAnalysis

logger = logging.getLogger(__name__)


def run_pipeline(db: Session) -> dict:
    results = []
    failed = []

    # top-level fetch guard — if Gmail itself fails, abort early
    try:
        emails = fetch_emails()
    except Exception as e:
        logger.error(f"[Pipeline] Email fetch failed entirely: {str(e)}")
        return {"processed": 0, "failed": 0, "results": [], "error": "Email fetch failed"}

    if not emails:
        logger.info("[Pipeline] No emails to process.")
        return {"processed": 0, "failed": 0, "results": []}

    for email_data in emails:
        subject = email_data.get("subject", "Unknown")
        analysis_record = None

        try:
            # step 1 — check for duplicates
            existing = db.query(Email).filter(
                Email.gmail_message_id == email_data["gmail_message_id"]
            ).first()

            if existing:
                logger.info(f"[Pipeline] Skipping duplicate: {email_data['gmail_message_id']}")
                continue

            # step 2 — store email in DB
            email_record = Email(
                gmail_message_id=email_data["gmail_message_id"],
                subject=email_data["subject"],
                sender=email_data["sender"],
                body=email_data["body"],
                received_at=email_data["received_at"]
            )
            db.add(email_record)
            db.commit()
            db.refresh(email_record)

            # step 3 — create analysis record with status "processing"
            # so if something fails mid-way, we have a record of it
            analysis_record = EmailAnalysis(
                email_id=email_record.id,
                status="processing"
            )
            db.add(analysis_record)
            db.commit()

            # step 4 — AI analysis
            ai_output = analyze_email(
                subject=email_data["subject"],
                sender=email_data["sender"],
                body=email_data["body"]
            )

            # step 5 — decision engine
            decision = process_email_decision(email_data, ai_output)

            # step 6 — execute automation action
            execute_action(decision["action"], email_record.id)

            # step 7 — update analysis record with results
            analysis_record.category = decision["category"]
            analysis_record.priority = decision["priority"]
            analysis_record.summary = decision["summary"]
            analysis_record.action_items = decision["action_items"]
            analysis_record.automation_action = decision["action"]
            analysis_record.status = "done"
            db.commit()

            results.append({
                "email_id": email_record.id,
                "subject": subject,
                "category": decision["category"],
                "priority": decision["priority"],
                "summary": decision["summary"],
                "action_items": decision["action_items"],
                "action": decision["action"],
                "description": decision["description"],
                "priority_overridden": decision["priority_overridden"]
            })

            logger.info(f"[Pipeline] Processed: {subject}")

        except SQLAlchemyError as e:
            logger.error(f"[Pipeline] DB error for '{subject}': {str(e)}")
            db.rollback()
            # if analysis record was already created, mark it failed
            try:
                if analysis_record and analysis_record.id:
                    analysis_record.status = "failed"
                    db.commit()
            except Exception:
                db.rollback()
            failed.append({"subject": subject, "reason": "database_error"})
            continue

        except Exception as e:
            logger.error(f"[Pipeline] Unexpected error for '{subject}': {str(e)}")
            db.rollback()
            try:
                if analysis_record and analysis_record.id:
                    analysis_record.status = "failed"
                    db.commit()
            except Exception:
                db.rollback()
            failed.append({"subject": subject, "reason": str(e)})
            continue

    logger.info(f"[Pipeline] Done — processed: {len(results)}, failed: {len(failed)}")

    return {
        "processed": len(results),
        "failed": len(failed),
        "results": results,
        "failures": failed
    }