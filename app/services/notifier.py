import logging
import requests
from typing import Optional

from app.config import SLACK_WEBHOOK_URL

logger = logging.getLogger(__name__)


def send_slack_notification(
    title: str,
    summary: str,
    action_items: list[str],
    sender: str,
    gmail_message_id: str,
) -> bool:
    """
    Send a Slack notification about an important email via incoming webhook.

    Args:
        title: Email subject
        summary: AI-generated summary
        action_items: List of action items extracted by AI
        sender: Email sender
        gmail_message_id: Gmail message ID (for deep linking)

    Returns:
        True if sent successfully, False if webhook unreachable or unconfigured.
    """
    if not SLACK_WEBHOOK_URL:
        logger.warning("[Notifier] SLACK_WEBHOOK_URL not configured — skipping notification")
        return False

    # Build Gmail deep link so user can click through
    gmail_link = f"https://mail.google.com/mail/u/0/#all/{gmail_message_id}"

    # Slack Block Kit format (richer than plain text)
    payload = {
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "📧 Important Email", "emoji": True},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*From:* {sender}\n*Subject:* {title}",
                },
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Summary:*\n{summary}"},
            },
        ]
    }

    # Add action items if any
    if action_items:
        items_text = "\n".join([f"• {item}" for item in action_items[:5]])  # cap at 5
        payload["blocks"].append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Action Items:*\n{items_text}"},
            }
        )

    # Add the Gmail link button
    payload["blocks"].append(
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "View in Gmail", "emoji": True},
                    "url": gmail_link,
                    "style": "primary",
                }
            ],
        }
    )

    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=5)
        if response.status_code == 200:
            logger.info("[Notifier] Slack notification sent successfully")
            return True
        else:
            logger.error(
                f"[Notifier] Slack returned {response.status_code}: {response.text}"
            )
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"[Notifier] Failed to send Slack notification: {e}")
        return False