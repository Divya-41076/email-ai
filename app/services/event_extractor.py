import logging
from datetime import datetime, timedelta
from icalendar import Calendar, Event

logger = logging.getLogger(__name__)


def build_ics(
    subject: str,
    event_datetime: str,
    duration_minutes: int,
    location_or_link: str,
) -> bytes:
    """
    Build an ICS (iCalendar) file for a calendar event.

    Args:
        subject: Event title
        event_datetime: ISO 8601 datetime (e.g. "2026-05-29T14:00:00+05:30")
        duration_minutes: Duration in minutes
        location_or_link: Location/room name or video link

    Returns:
        ICS file content as bytes.

    Raises:
        ValueError: If event_datetime is invalid.
    """
    try:
        # Parse the ISO datetime — handle 'Z' suffix and timezone offsets
        dt_str = event_datetime.replace("Z", "+00:00")
        dt_start = datetime.fromisoformat(dt_str)
    except (ValueError, TypeError) as e:
        logger.error(f"[EventExtractor] Failed to parse event_datetime '{event_datetime}': {e}")
        raise ValueError(f"Invalid datetime: {event_datetime}") from e

    # Calculate end time
    dt_end = dt_start + timedelta(minutes=duration_minutes)

    # Build the calendar
    cal = Calendar()
    cal.add("prodid", "-//InboxIQ//Email to Calendar//EN")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")

    # Build the event
    event = Event()
    event.add("summary", subject)
    event.add("dtstart", dt_start)
    event.add("dtend", dt_end)
    if location_or_link:
        event.add("location", location_or_link)
    event.add("description", f"Meeting extracted by InboxIQ from email.\nLocation/Link: {location_or_link or 'Not specified'}")
    event.add("uid", f"{subject}@email-ai-{dt_start.timestamp()}")  # unique id

    cal.add_component(event)

    # Serialize to ICS format
    ics_bytes = cal.to_ical()
    logger.info(
        f"[EventExtractor] Built ICS: subject='{subject}', "
        f"datetime={event_datetime}, duration={duration_minutes}min, location='{location_or_link}'"
    )

    return ics_bytes