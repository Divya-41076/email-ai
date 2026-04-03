import logging

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────
# AUTOMATION ACTIONS
# ─────────────────────────────────────────

def mark_priority(email_id: int):
    logger.info(f"[Automation] Email {email_id} marked as priority")
    return {"status": "success", "action": "mark_priority", "email_id": email_id}


def mark_priority_and_notify(email_id: int):
    logger.info(f"[Automation] Email {email_id} marked as priority + notification triggered")
    # Future: send Slack/email notification here
    return {"status": "success", "action": "mark_priority_and_notify", "email_id": email_id}


def extract_event(email_id: int):
    logger.info(f"[Automation] Email {email_id} meeting event extracted")
    # Future: integrate with Google Calendar here
    return {"status": "success", "action": "extract_event", "email_id": email_id}


def extract_event_and_notify(email_id: int):
    logger.info(f"[Automation] Email {email_id} meeting event extracted + notification triggered")
    # Future: integrate with Google Calendar + notify here
    return {"status": "success", "action": "extract_event_and_notify", "email_id": email_id}


def archive_email(email_id: int):
    logger.info(f"[Automation] Email {email_id} archived")
    # Future: apply Gmail archive label here
    return {"status": "success", "action": "archive", "email_id": email_id}


def mark_read(email_id: int):
    logger.info(f"[Automation] Email {email_id} marked as read")
    # Future: apply Gmail read status here
    return {"status": "success", "action": "mark_read", "email_id": email_id}


def delete_email(email_id: int):
    logger.info(f"[Automation] Email {email_id} deleted")
    # Future: move to Gmail trash here
    return {"status": "success", "action": "delete", "email_id": email_id}


def inbox(email_id: int):
    logger.info(f"[Automation] Email {email_id} left in inbox")
    return {"status": "success", "action": "inbox", "email_id": email_id}


# ─────────────────────────────────────────
# ACTION DISPATCHER
# ─────────────────────────────────────────

ACTION_MAP = {
    "mark_priority":            mark_priority,
    "mark_priority_and_notify": mark_priority_and_notify,
    "extract_event":            extract_event,
    "extract_event_and_notify": extract_event_and_notify,
    "archive":                  archive_email,
    "mark_read":                mark_read,
    "delete":                   delete_email,
    "inbox":                    inbox
}


def execute_action(action: str, email_id: int) -> dict:
    handler = ACTION_MAP.get(action)

    if not handler:
        logger.warning(f"[Automation] Unknown action: {action} for email {email_id}")
        return {"status": "unknown_action", "action": action, "email_id": email_id}

    return handler(email_id)