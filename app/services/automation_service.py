import logging
from googleapiclient.errors import HttpError

from app.services.gmail_client import GmailClient
from app.services.notifier import send_slack_notification
from app.services.event_extractor import build_ics

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────
# AUTOMATION ACTIONS
# ─────────────────────────────────────────
# Each handler accepts a uniform signature:
#   client            — GmailClient instance (one per pipeline run)
#   gmail_message_id  — Gmail's message ID, used for actual API mutations
#   db_email_id       — our DB row id, used for logging and result tracking
#   email_context     - which is used only mainly by notify and impotant

# ----- ACTION HANDLERS -----


# ----mark_priority----
def mark_priority(
    client: GmailClient, gmail_message_id: str, db_email_id: int, email_context: dict
) -> dict:
    try:
        client.add_label(gmail_message_id, ["STARRED", "IMPORTANT"])
        logger.info(
            f"[Automation] mark_priority stub — gmail_id={gmail_message_id}, db_id={db_email_id}"
        )
        return {"status": "success", "action": "mark_priority", "email_id": db_email_id}
    except HttpError as e:
        logger.error(f"[Automation] mark_priority failed db_id={db_email_id}: {e}")
        return {
            "status": "error",
            "action": "mark_priority",
            "email_id": db_email_id,
            "error": str(e),
        }


# ----mark_priority_and_notify----
def mark_priority_and_notify(
    client: GmailClient, gmail_message_id: str, db_email_id: int, email_context: dict
) -> dict:
    try:
        client.add_label(gmail_message_id, ["STARRED", "IMPORTANT"])
        logger.info(
            f"[Automation] Starred db_id={db_email_id} gmail_id={gmail_message_id}"
        )

        notification_sent = send_slack_notification(
            title=email_context.get("subject", "Unknown"),
            summary=email_context.get("summary", ""),
            action_items=email_context.get("action_items", []),
            sender=email_context.get("sender", "Unknown"),
            gmail_message_id=gmail_message_id,
        )

        return {
            "status": "success",
            "action": "mark_priority_and_notify",
            "email_id": db_email_id,
        }

    except HttpError as e:
        logger.error(
            f"[Automation] mark_priority_and_notify failed db_id={db_email_id:{e}}"
        )
        return {
            "status": "error",
            "action": "mark_priority_and_notify",
            "email_id": db_email_id,
            "error": str(e),
        }


# ----extract_event----
def extract_event(
    client: GmailClient,
    gmail_message_id: str,
    db_email_id: int,
    email_context: dict,
) -> dict:
    """
    Extract meeting details from email and generate an ICS calendar file.

    If the AI extracted event_datetime, builds an ICS and saves to disk.
    If no event_datetime was extracted, gracefully skips (returns success with no file).
    """
    event_datetime = email_context.get("event_datetime")

    # Graceful degradation: if we don't have a datetime, can't build an event
    if not event_datetime:
        logger.info(
            f"[Automation] extract_event skipped for db_id={db_email_id} — "
            f"no event_datetime extracted by AI"
        )
        return {"status": "success", "action": "extract_event", "email_id": db_email_id}

    try:
        from app.services.event_extractor import build_ics
        import os

        subject = email_context.get("subject", "Meeting")
        duration_minutes = email_context.get("duration_minutes") or 60
        location_or_link = email_context.get("location_or_link") or "Not specified"

        # Build ICS file in memory
        ics_bytes = build_ics(
            subject=subject,
            event_datetime=event_datetime,
            duration_minutes=duration_minutes,
            location_or_link=location_or_link,
        )

        # Save to local meetings/ directory
        # NOTE: For production (Phase 5+), this should be S3, not local disk
        meetings_dir = "meetings"
        os.makedirs(meetings_dir, exist_ok=True)
        ics_file_path = f"{meetings_dir}/meeting_{db_email_id}.ics"
        with open(ics_file_path, "wb") as f:
            f.write(ics_bytes)

        logger.info(
            f"[Automation] extract_event completed db_id={db_email_id} — "
            f"ICS saved to {ics_file_path}"
        )
        return {
            "status": "success",
            "action": "extract_event",
            "email_id": db_email_id,
            "ics_file_path": ics_file_path,
        }

    except Exception as e:
        logger.error(f"[Automation] extract_event failed db_id={db_email_id}: {e}")
        return {
            "status": "error",
            "action": "extract_event",
            "email_id": db_email_id,
            "error": str(e),
        }


# ---extract_event_and_notify----
def extract_event_and_notify(
    client: GmailClient, gmail_message_id: str, db_email_id: int, email_context: dict
) -> dict:
    """
    Extract meeting event + send Slack notification.

    Reuses extract_event for the ICS generation, then adds notification.
    """
    # First extract the event
    extract_result = extract_event(client, gmail_message_id, db_email_id, email_context)

    if extract_result["status"] != "success":
        # Event extraction failed, don't try to notify
        return extract_result

    # Event extraction succeeded, now send notification
    notification_sent = send_slack_notification(
        title=email_context.get("subject", "Meeting"),
        summary=email_context.get("summary", ""),
        action_items=email_context.get("action_items", []),
        sender=email_context.get("sender", "Unknown"),
        gmail_message_id=gmail_message_id,
    )

    return {
        "status": "success",
        "action": "extract_event_and_notify",
        "email_id": db_email_id,
        "ics_file_path": extract_result.get("ics_file_path"),
        "notification_sent": notification_sent,
    }


# ----archive_email----
def archive_email(
    client: GmailClient, gmail_message_id: str, db_email_id: int, email_context: dict
) -> dict:
    """Remove INBOX label — email still findable in All Mail."""
    try:
        client.remove_label(gmail_message_id, "INBOX")
        logger.info(
            f"[Automation] Archived db_id={db_email_id} gmail_id={gmail_message_id}"
        )
        return {"status": "success", "action": "archive", "email_id": db_email_id}
    except HttpError as e:
        logger.error(f"[Automation] archive failed db_id={db_email_id}: {e}")
        return {
            "status": "error",
            "action": "archive",
            "email_id": db_email_id,
            "error": str(e),
        }


# ----mark_read----
def mark_read(
    client: GmailClient, gmail_message_id: str, db_email_id: int, email_context: dict
) -> dict:
    """Remove UNREAD label."""
    try:
        client.remove_label(gmail_message_id, "UNREAD")
        logger.info(
            f"[Automation] Marked read db_id={db_email_id} gmail_id={gmail_message_id}"
        )
        return {"status": "success", "action": "mark_read", "email_id": db_email_id}
    except HttpError as e:
        logger.error(f"[Automation] mark_read failed db_id={db_email_id}: {e}")
        return {
            "status": "error",
            "action": "mark_read",
            "email_id": db_email_id,
            "error": str(e),
        }


# ---delete_email----
def delete_email(
    client: GmailClient, gmail_message_id: str, db_email_id: int, email_context: dict
) -> dict:
    """Move email to Trash (Gmail keeps trashed messages for 30 days before permanent deletion)."""
    try:
        client.trash(gmail_message_id)
        logger.info(
            f"[Automation] Trashed db_id={db_email_id} gmail_id={gmail_message_id}"
        )
        return {"status": "success", "action": "delete", "email_id": db_email_id}
    except HttpError as e:
        logger.error(f"[Automation] delete failed db_id={db_email_id}: {e}")
        return {
            "status": "error",
            "action": "delete",
            "email_id": db_email_id,
            "error": str(e),
        }


# ---inbox (no-op, just for testing)----
def inbox(
    client: GmailClient, gmail_message_id: str, db_email_id: int, email_context: dict
) -> dict:
    logger.info(
        f"[Automation] inbox no-op — gmail_id={gmail_message_id}, db_id={db_email_id}"
    )
    return {"status": "success", "action": "inbox", "email_id": db_email_id}


# ─────────────────────────────────────────
# ACTION DISPATCHER
# ─────────────────────────────────────────

ACTION_MAP = {
    "mark_priority": mark_priority,
    "mark_priority_and_notify": mark_priority_and_notify,
    "extract_event": extract_event,
    "extract_event_and_notify": extract_event_and_notify,
    "archive": archive_email,
    "mark_read": mark_read,
    "delete": delete_email,
    "inbox": inbox,
}


# Uniform interface for executing an action by name, with error handling and logging
def execute_action(
    action: str,
    client: GmailClient,
    gmail_message_id: str,
    db_email_id: int,
    email_context: dict,
) -> dict:
    handler = ACTION_MAP.get(action)

    if not handler:
        logger.warning(
            f"[Automation] Unknown action '{action}' for db_id={db_email_id}"
        )
        return {"status": "unknown_action", "action": action, "email_id": db_email_id}

    return handler(client, gmail_message_id, db_email_id, email_context)
