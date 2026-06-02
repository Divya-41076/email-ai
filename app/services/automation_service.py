import logging
from googleapiclient.errors import HttpError

from app.services.gmail_client import GmailClient

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────
# AUTOMATION ACTIONS
# ─────────────────────────────────────────
# Each handler accepts a uniform signature:
#   client            — GmailClient instance (one per pipeline run)
#   gmail_message_id  — Gmail's message ID, used for actual API mutations
#   db_email_id       — our DB row id, used for logging and result tracking

def mark_priority(client: GmailClient, gmail_message_id: str, db_email_id: int) -> dict:
    try:
        client.add_label(gmail_message_id,["STARRED","IMPORTANT"])
        logger.info(f"[Automation] mark_priority stub — gmail_id={gmail_message_id}, db_id={db_email_id}")
        return {"status": "success", "action": "mark_priority", "email_id": db_email_id}
    except HttpError as e:
        logger.error(f"[Automation] mark_priority failed db_id={db_email_id}: {e}")
        return {"status": "error", "action":"mark_priority","email_id":db_email_id, "error":str(e)}

def mark_priority_and_notify(client: GmailClient, gmail_message_id: str, db_email_id: int) -> dict:
    try:
        client.add_label(gmail_message_id,["STARRED","IMPORTANT"])
        logger.info(f"[Automation] Starred db_id={db_email_id} gmail_id={gmail_message_id}")
        logger.info(f"[Automation] Notify placeholder for db_id={db_email_id} - real slack in phase 2")
        logger.info(f"[Automation] mark_priority_and_notify stub — gmail_id={gmail_message_id}, db_id={db_email_id}")
        return {"status": "success", "action": "mark_priority_and_notify", "email_id": db_email_id}
    except HttpError as e:
        logger.error(f"[Automation] mark_priority_and_notify failed db_id={db_email_id:{e}}")
        return {"status": "error", "action": "mark_priority_and_notify", "email_id": db_email_id, "error":str(e)}

def extract_event(client: GmailClient, gmail_message_id: str, db_email_id: int) -> dict:
    logger.info(f"[Automation] extract_event stub — gmail_id={gmail_message_id}, db_id={db_email_id}")
    return {"status": "success", "action": "extract_event", "email_id": db_email_id}

def extract_event_and_notify(client: GmailClient, gmail_message_id: str, db_email_id: int) -> dict:
    logger.info(f"[Automation] extract_event_and_notify stub — gmail_id={gmail_message_id}, db_id={db_email_id}")
    return {"status": "success", "action": "extract_event_and_notify", "email_id": db_email_id}


def archive_email(client: GmailClient, gmail_message_id: str, db_email_id: int) -> dict:
    """Remove INBOX label — email still findable in All Mail."""
    try:
        client.remove_label(gmail_message_id, "INBOX")
        logger.info(f"[Automation] Archived db_id={db_email_id} gmail_id={gmail_message_id}")
        return {"status": "success", "action": "archive", "email_id": db_email_id}
    except HttpError as e:
        logger.error(f"[Automation] archive failed db_id={db_email_id}: {e}")
        return {"status": "error", "action": "archive", "email_id": db_email_id, "error": str(e)}

def mark_read(client: GmailClient, gmail_message_id: str, db_email_id: int) -> dict:
    """Remove UNREAD label."""
    try:
        client.remove_label(gmail_message_id, "UNREAD")
        logger.info(f"[Automation] Marked read db_id={db_email_id} gmail_id={gmail_message_id}")
        return {"status": "success", "action": "mark_read", "email_id": db_email_id}
    except HttpError as e:
        logger.error(f"[Automation] mark_read failed db_id={db_email_id}: {e}")
        return {"status": "error", "action": "mark_read", "email_id": db_email_id, "error": str(e)}

def delete_email(client: GmailClient, gmail_message_id: str, db_email_id: int) -> dict:
    """Move email to Trash (Gmail keeps trashed messages for 30 days before permanent deletion)."""
    try:
        client.trash(gmail_message_id)
        logger.info(f"[Automation] Trashed db_id={db_email_id} gmail_id={gmail_message_id}")
        return {"status": "success", "action": "delete", "email_id": db_email_id}
    except HttpError as e:
        logger.error(f"[Automation] delete failed db_id={db_email_id}: {e}")
        return {"status": "error", "action": "delete", "email_id": db_email_id, "error": str(e)}


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