import logging

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────
# 1. CONFIGURATION
# ─────────────────────────────────────────

IMPORTANT_CONTACTS = {
    "boss@company.com",
    "hr@amazon.com",
    "hr@google.com",
    "hr@microsoft.com"
}

HIGH_PRIORITY_KEYWORDS = [
    "interview", "offer", "urgent", "asap",
    "deadline", "immediate", "action required",
    "job offer", "selected", "congratulations"
]

LOW_PRIORITY_KEYWORDS = [
    "unsubscribe", "newsletter", "weekly digest",
    "no-reply", "promotion", "sale", "discount"
]

# ─────────────────────────────────────────
# 2. DECISION MATRIX
# ─────────────────────────────────────────

DECISION_MATRIX = {
    "Job Opportunity": {
        "High":   "mark_priority_and_notify",
        "Medium": "mark_priority",
        "Low":    "inbox"
    },
    "Meeting": {
        "High":   "extract_event_and_notify",
        "Medium": "extract_event",
        "Low":    "extract_event"
    },
    "Newsletter": {
        "High":   "inbox",
        "Medium": "archive",
        "Low":    "archive"
    },
    "Promotion": {
        "High":   "archive",
        "Medium": "archive",
        "Low":    "delete"
    },
    "Notification": {
        "High":   "mark_priority",
        "Medium": "mark_read",
        "Low":    "mark_read"
    },
    "Personal": {
        "High":   "mark_priority",
        "Medium": "inbox",
        "Low":    "inbox"
    },
    "Spam": {
        "High":   "delete",
        "Medium": "delete",
        "Low":    "delete"
    },
    "Other": {
        "High":   "inbox",
        "Medium": "inbox",
        "Low":    "inbox"
    }
}

ACTION_DESCRIPTIONS = {
    "mark_priority":            "Marked as priority",
    "mark_priority_and_notify": "Marked as priority and notification triggered",
    "extract_event":            "Meeting event extracted",
    "extract_event_and_notify": "Meeting event extracted and notification triggered",
    "archive":                  "Archived automatically",
    "mark_read":                "Marked as read",
    "delete":                   "Deleted automatically",
    "inbox":                    "Left in inbox"
}

# ─────────────────────────────────────────
# 3. PRIORITY ENGINE
# ─────────────────────────────────────────

def apply_priority_rules(email: dict, ai_priority: str) -> str:
    subject = email.get("subject", "").lower()
    sender = email.get("sender", "").lower()
    body = email.get("body", "").lower()
    full_text = f"{subject} {body}"

    # rule 1 — important sender always high
    if sender in IMPORTANT_CONTACTS:
        logger.info(f"[Priority] Overridden to High — important contact: {sender}")
        return "High"

    # rule 2 — high priority keywords found
    for keyword in HIGH_PRIORITY_KEYWORDS:
        if keyword in full_text:
            logger.info(f"[Priority] Overridden to High — keyword: '{keyword}'")
            return "High"

    # rule 3 — low priority keywords found
    for keyword in LOW_PRIORITY_KEYWORDS:
        if keyword in full_text:
            logger.info(f"[Priority] Overridden to Low — keyword: '{keyword}'")
            return "Low"

    # rule 4 — trust AI priority
    logger.info(f"[Priority] Using AI priority: {ai_priority}")
    return ai_priority

# ─────────────────────────────────────────
# 4. DECISION ENGINE
# ─────────────────────────────────────────

def get_automation_action(category: str, priority: str) -> dict:
    category = category.strip().title()
    priority = priority.strip().title()

    if category not in DECISION_MATRIX:
        category = "Other"

    if priority not in ["High", "Medium", "Low"]:
        priority = "Medium"

    action = DECISION_MATRIX[category][priority]
    description = ACTION_DESCRIPTIONS.get(action, "Processed")

    logger.info(f"[Decision] {category} | {priority} → {action}")

    return {
        "action": action,
        "description": description,
        "category": category,
        "priority": priority
    }

# ─────────────────────────────────────────
# 5. MAIN PIPELINE FUNCTION
# ─────────────────────────────────────────

def process_email_decision(email: dict, ai_output: dict) -> dict:
    """
    email = {
        "subject": "...",
        "sender": "...",
        "body": "..."
    }
    ai_output = {
        "category": "...",
        "priority": "...",
        "summary": "...",
        "action_items": [...]
    }
    """
    category = ai_output.get("category", "Other")
    ai_priority = ai_output.get("priority", "Medium")

    # apply rule based priority override
    final_priority = apply_priority_rules(email, ai_priority)

    # get action from decision matrix
    result = get_automation_action(category, final_priority)

    # attach AI outputs to final result
    result["summary"] = ai_output.get("summary", "")
    result["action_items"] = ai_output.get("action_items", [])
    result["priority_overridden"] = final_priority != ai_priority

    logger.info(f"[Pipeline] Complete → {result['action']}")

    return result


'''
response
    {
    "email": {
        "id": 1,
        "subject": "Backend Engineer Interview Invitation",
        "sender": "recruiter@google.com",
        "received_at": "2024-01-15T10:30:00"
    },
    "analysis": {
        "category": "Job Opportunity",
        "priority": "High",
        "summary": "Recruiter from Google invited you for a backend engineer interview next Tuesday",
        "action_items": [
            "Confirm availability",
            "Prepare system design",
            "Research the company"
        ],
        "action": "mark_priority_and_notify",
        "description": "Marked as priority and notification triggered",
        "priority_overridden": true
    }
}

'''