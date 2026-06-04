import base64
import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.utils.gmail_auth import get_gmail_credentials

logger = logging.getLogger(__name__)


def _extract_body(payload: dict) -> str:
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
        data = payload.get("body", {}).get("data", "")
        if data:
            body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

    return body.strip()


def _parse_email_date(date_str: str) -> datetime:
    """Parse the RFC 2822 Date header; fall back to current UTC time on failure."""
    if not date_str:
        return datetime.now(timezone.utc)
    try:
        parsed = parsedate_to_datetime(date_str)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except (TypeError, ValueError) as e:
        logger.warning(f"[GmailClient] Could not parse Date header '{date_str}': {e}")
        return datetime.now(timezone.utc)


class GmailClient:
    """
    Thin wrapper around the Gmail API service.

    Holds a single authenticated service instance and exposes both read
    operations (fetch_unread) and write primitives (add_label, remove_label,
    trash) used by the automation service.

    Lifetime: one instance per pipeline run. Not thread-safe — do not share
    across concurrent runs.
    """

    def __init__(self):
        creds = get_gmail_credentials()
        self.service = build("gmail", "v1", credentials=creds)
        logger.debug("[GmailClient] Service initialized")

    # ─── READ ────────────────────────────────────────────────────────

    def fetch_unread(self, max_results: int = 10) -> list[dict]:
        """
        Fetch up to `max_results` unread inbox emails.

        Per-message failures are caught and skipped. System-level failures
        (auth, network) propagate to the caller.
        """
        results = self.service.users().messages().list(
            userId="me",
            labelIds=["INBOX"],
            q="is:unread",
            maxResults=max_results,
        ).execute()

        messages = results.get("messages", [])
        logger.info(f"[GmailClient] Gmail returned {len(messages)} unread message(s)")

        if not messages:
            return []

        emails = []
        for msg in messages:
            try:
                msg_data = self.service.users().messages().get(
                    userId="me",
                    id=msg["id"],
                    format="full",
                ).execute()

                headers = msg_data["payload"]["headers"]
                subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
                sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
                date_str = next((h["value"] for h in headers if h["name"] == "Date"), None)
                body = _extract_body(msg_data["payload"])

                emails.append({
                    "gmail_message_id": msg["id"],
                    "subject": subject,
                    "sender": sender,
                    "body": body[:2000],
                    "received_at": _parse_email_date(date_str),
                })
            except HttpError as e:
                logger.error(f"[GmailClient] Failed to fetch message {msg['id']}: {e}")
                continue

        logger.info(f"[GmailClient] Successfully fetched {len(emails)} email(s)")
        return emails

    # ─── WRITE PRIMITIVES (used by automation_service) ───────────────

    def add_label(self, gmail_message_id: str, labels: str) -> None:
        """Add one or more Gmail label (e.g. 'STARRED') to a message."""
        
        if isinstance(labels,str):
            labels = [labels]
        self.service.users().messages().modify(
            userId="me",
            id=gmail_message_id,
            body={"addLabelIds": [labels]},
        ).execute()

    def remove_label(self, gmail_message_id: str, label: str) -> None:
        """Remove a Gmail label (e.g. 'INBOX', 'UNREAD') from a message."""
        self.service.users().messages().modify(
            userId="me",
            id=gmail_message_id,
            body={"removeLabelIds": [label]},
        ).execute()

    def trash(self, gmail_message_id: str) -> None:
        """Move a message to Trash. Reversible for 30 days."""
        self.service.users().messages().trash(
            userId="me",
            id=gmail_message_id,
        ).execute()