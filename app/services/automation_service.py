import logging
from app.services.gmail_client import GmailClient

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────
# AUTOMATION ACTIONS
# ─────────────────────────────────────────
# Each handler accepts a uniform signature:
#   client            — GmailClient instance (one per pipeline run)
#   gmail_message_id  — Gmail's message ID, used for actual API mutations
#   db_email_id       — our DB row id, used for logging and result tracking
#
# Chunk 2 keeps the bodies as stubs (logger calls only).
# Chunk 3 wires real Gmail API calls via the GmailClient primitives.

def mark_priority(client: GmailClient, gmail_message_id: str, db_email_id: int) -> dict:
    logger.info(f"[Automation] mark_priority stub — gmail_id={gmail_message_id}, db_id={db_email_id}")
    return {"status": "success", "action": "mark_priority", "email_id": db_email_id}


def mark_priority_and_notify(client: GmailClient, gmail_message_id: str, db_email_id: int) -> dict:
    logger.info(f"[Automation] mark_priority_and_notify stub — gmail_id={gmail_message_id}, db_id={db_email_id}")
    return {"status": "success", "action": "mark_priority_and_notify", "email_id": db_email_id}


def extract_event(client: GmailClient, gmail_message_id: str, db_email_id: int) -> dict:
    logger.info(f"[Automation] extract_event stub — gmail_id={gmail_message_id}, db_id={db_email_id}")
    return {"status": "success", "action": "extract_event", "email_id": db_email_id}


def extract_event_and_notify(client: GmailClient, gmail_message_id: str, db_email_id: int) -> dict:
    logger.info(f"[Automation] extract_event_and_notify stub — gmail_id={gmail_message_id}, db_id={db_email_id}")
    return {"status": "success", "action": "extract_event_and_notify", "email_id": db_email_id}


def archive_email(client: GmailClient, gmail_message_id: str, db_email_id: int) -> dict:
    logger.info(f"[Automation] archive_email stub — gmail_id={gmail_message_id}, db_id={db_email_id}")
    return {"status": "success", "action": "archive", "email_id": db_email_id}


def mark_read(client: GmailClient, gmail_message_id: str, db_email_id: int) -> dict:
    logger.info(f"[Automation] mark_read stub — gmail_id={gmail_message_id}, db_id={db_email_id}")
    return {"status": "success", "action": "mark_read", "email_id": db_email_id}


def delete_email(client: GmailClient, gmail_message_id: str, db_email_id: int) -> dict:
    logger.info(f"[Automation] delete_email stub — gmail_id={gmail_message_id}, db_id={db_email_id}")
    return {"status": "success", "action": "delete", "email_id": db_email_id}


def inbox(client: GmailClient, gmail_message_id: str, db_email_id: int) -> dict:
    logger.info(f"[Automation] inbox no-op — gmail_id={gmail_message_id}, db_id={db_email_id}")
    return {"status": "success", "action": "inbox", "email_id": db_email_id}


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
    "inbox":                    inbox,
}


def execute_action(action: str, client: GmailClient, gmail_message_id: str, db_email_id: int) -> dict:
    handler = ACTION_MAP.get(action)

    if not handler:
        logger.warning(f"[Automation] Unknown action '{action}' for db_id={db_email_id}")
        return {"status": "unknown_action", "action": action, "email_id": db_email_id}

    return handler(client, gmail_message_id, db_email_id)