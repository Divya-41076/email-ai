import logging
from datetime import datetime
from googleapiclient.discovery import build # builds gmail api client service obj to talk to gmail
from app.utils.gmail_auth import get_gmail_credentials #validates the credentials login/refresh token

import base64 #gmail sends emailbody encoded so we must decode it
import email as email_parser

logger = logging.getLogger(__name__)

#extracting email body
def get_email_body(payload):
    body = ""

    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                data = part["body"].get("data", "")

                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                    break

    else:#sm email dont hv parts, directly hv the body
        data = payload.get("body", {}).get("data", "")
        if data:
            body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

            
    return body.strip()

#MAIN FLOWWWWW
def fetch_emails(max_results: int = 10):
    try:
        creds = get_gmail_credentials()#gets auth code from before and validates it, refreshes if expired, or starts auth flow if no valid token

        print(f"CREDS VALID: {creds.valid}")
        print(f"CREDS EXPIRED: {creds.expired}")

        service = build("gmail", "v1", credentials=creds)#creates the GMAIL API client service obj to talk to gmail api

        # fetch unread emails max upto 10 emails
        results = service.users().messages().list(
            userId="me",
            labelIds=["INBOX"],
            q="is:unread",
            maxResults=max_results
        ).execute()

        print(f"RAW RESULTS: {results}")

        messages = results.get("messages", [])
        print(F"gmail returned:{len(messages)} messages")

        if not messages:
            logger.info("[Fetcher] No unread emails found")
            return []

        emails = []
        for msg in messages:
            msg_data = service.users().messages().get(
                userId="me",
                id=msg["id"],
                format="full"
            ).execute()

            headers = msg_data["payload"]["headers"]
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
            sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
            date_str = next((h["value"] for h in headers if h["name"] == "Date"), None)

            #a generator expression that iterates through the headers
            # produces values one-by-one(lazy) instead of creating a full list in memory

            body = get_email_body(msg_data["payload"])

            emails.append({
                "gmail_message_id": msg["id"],
                "subject": subject,
                "sender": sender,
                "body": body[:2000],  # limit body length
                "received_at": datetime.utcnow()
            })

        logger.info(f"[Fetcher] Fetched {len(emails)} emails")
        return emails

    except Exception as e:
        logger.error(f"[Fetcher] Failed to fetch emails: {str(e)}")
        return []
























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