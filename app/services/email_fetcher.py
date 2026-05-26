import base64
import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.utils.gmail_auth import get_gmail_credentials

logger = logging.getLogger(__name__)

# helper func
def get_email_body(payload: dict) -> str:
    """Extract plain-text body from a Gmail message payload."""
    body = ""

    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                data = part["body"].get("data", "")
                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                    break
    else:
        # Some emails don't have parts — body is at the top level
        data = payload.get("body", {}).get("data", "")
        if data:
            body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

    return body.strip()

# helper func 
def parse_email_date(date_str: str) -> datetime:
    """Parse the RFC 2822 Date header from an email. Falls back to now on failure."""
    if not date_str:
        return datetime.now(timezone.utc)
    try:
        parsed = parsedate_to_datetime(date_str)
        # Ensure timezone-aware
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except (TypeError, ValueError) as e:
        logger.warning(f"[Fetcher] Could not parse Date header '{date_str}': {e}")
        return datetime.now(timezone.utc)


def fetch_emails(max_results: int = 10) -> list[dict]:
    """
    Fetch up to `max_results` unread inbox emails from Gmail.

    Raises:
        - googleapiclient.errors.HttpError on Gmail API failures
        - google.auth.exceptions.RefreshError on OAuth token issues
        - Other exceptions propagate to the caller (pipeline guards against them)
    """
    creds = get_gmail_credentials()
    service = build("gmail", "v1", credentials=creds)

    # fetch unread emails, max upto `max_results`
    results = service.users().messages().list(
        userId="me",
        labelIds=["INBOX"],
        q="is:unread",
        maxResults=max_results,
    ).execute()

    messages = results.get("messages", [])
    logger.info(f"[Fetcher] Gmail returned {len(messages)} unread message(s)")

    if not messages:
        return []

    emails = []
    for msg in messages:
        try:
            msg_data = service.users().messages().get(
                userId="me",
                id=msg["id"],
                format="full",
            ).execute()

            headers = msg_data["payload"]["headers"]
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
            sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
            date_str = next((h["value"] for h in headers if h["name"] == "Date"), None)

            body = get_email_body(msg_data["payload"])

            emails.append({
                "gmail_message_id": msg["id"],
                "subject": subject,
                "sender": sender,
                "body": body[:2000],  # cap body length to control LLM token usage
                "received_at": parse_email_date(date_str),
            })
        except HttpError as e:
            # Per-message failure: log and skip, don't fail the whole batch
            logger.error(f"[Fetcher] Failed to fetch message {msg['id']}: {e}")
            continue

    logger.info(f"[Fetcher] Successfully fetched {len(emails)} email(s)")
    return emails























# import logging
# from datetime import datetime

# logger = logging.getLogger(__name__)

# # ─────────────────────────────────────────
# # DUMMY EMAIL FETCHER (Phase 6)
# # Real Gmail fetcher comes in Phase 8
# # ─────────────────────────────────────────

# DUMMY_EMAILS = [
#     {
#         "gmail_message_id": "dummy_001",
#         "subject": "Backend Engineer Interview Invitation",
#         "sender": "recruiter@google.com",
#         "body": "Hi, we would like to invite you for a backend engineer interview next Tuesday. Please confirm your availability.",
#         "received_at": datetime.utcnow()
#     },
#     {
#         "gmail_message_id": "dummy_002",
#         "subject": "Your weekly tech newsletter",
#         "sender": "newsletter@techdigest.com",
#         "body": "This week in tech: AI breakthroughs, new Python releases, and cloud computing trends. Unsubscribe here.",
#         "received_at": datetime.utcnow()
#     },
#     {
#         "gmail_message_id": "dummy_003",
#         "subject": "Team standup tomorrow at 10am",
#         "sender": "manager@company.com",
#         "body": "Hey team, reminder that we have our weekly standup tomorrow at 10am. Please be on time.",
#         "received_at": datetime.utcnow()
#     }
# ]


# def fetch_emails():
#     logger.info(f"[Fetcher] Fetching {len(DUMMY_EMAILS)} dummy emails")
#     return DUMMY_EMAILS