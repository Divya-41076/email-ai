import json
import re
import logging

from groq import Groq
from app.config import GROQ_API_KEY
from app.utils.prompts import EMAIL_ANALYSIS_PROMPT
from datetime import datetime,date

logger = logging.getLogger(__name__)
# create a groq client
client = Groq(api_key=GROQ_API_KEY)

VALID_CATEGORIES = [
    "Job Opportunity", "Meeting", "Newsletter",
    "Notification", "Promotion", "Personal", "Spam", "Other"
]
VALID_PRIORITIES = ["High", "Medium", "Low"]

def validate_analysis(result:dict) ->dict:
    validated = {
        "category": result.get("category", "Other"),
        "priority": result.get("priority", "Low"),
        "summary": result.get("summary", "No summary available."),
        "action_items": result.get("action_items", []),
        "event_datetime": result.get("event_datetime"),
        "duration_minutes": result.get("duration_minutes"),
        "location_or_link": result.get("location_or_link"),

    }

    # validate category is an allowed value
    if validated["category"] not in VALID_CATEGORIES:
        validated["category"] = "Other"

    # validate priority is an allowed value
    if validated["priority"] not in VALID_PRIORITIES:
        validated["priority"] = "Low"

    # ensure summary is a string
    if not isinstance(validated["summary"], str):
        validated["summary"] = "No summary available."

    # ensure action_items is a list of strings
    if not isinstance(validated["action_items"], list):
        validated["action_items"] = []
    else:
        validated["action_items"] = [
            str(item) for item in validated["action_items"]
            if item
        ][:5]  # max 5 items
    
    # validate the event date time
    if validated["event_datetime"] is not None:
        if isinstance(validated["event_datetime"], str):
            try:
                dt_str = validated["event_datetime"].replace("Z", "+00:00")
                datetime.fromisoformat(dt_str)

            except (ValueError, TypeError) as e:
                logger.warning(f"[Analyser] Invalid event_datetime '{validated['event_datetime']}': {e} - setting to null")
                validated["event_datetime"] = None
        else:
            # not a string set to null
            validated["event_datetime"] = None

     #  Validate duration_minutes (positive int or null) 
    if validated["duration_minutes"] is not None:
        try:
            duration = int(validated["duration_minutes"])
            if duration > 0:
                validated["duration_minutes"] = duration
            else:
                logger.warning(
                    f"[Analyzer] Invalid duration_minutes {duration}: must be > 0 — setting to null"
                )
                validated["duration_minutes"] = None
        except (ValueError, TypeError):
            logger.warning(
                f"[Analyzer] Invalid duration_minutes '{validated['duration_minutes']}': not an integer — setting to null"
            )
            validated["duration_minutes"] = None  

     #  Validate location_or_link (string or null) 
    if validated["location_or_link"] is not None:
        if isinstance(validated["location_or_link"], str):
            validated["location_or_link"] = validated["location_or_link"].strip()
            # If empty after stripping, set to null
            if not validated["location_or_link"]:
                validated["location_or_link"] = None
        else:
            # Not a string, set to null
            validated["location_or_link"] = None



    return validated



def analyze_email(subject:str,sender:str,body:str)->dict:
    # return type is dict with keys

    # build the prompt

    current_date = date.today().isoformat()
    prompt = EMAIL_ANALYSIS_PROMPT.format(
        subject=subject,
        sender=sender,
        body=body,
        current_date=current_date
    )
    try:
    # call groqapi

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role":"user", "content":prompt
                }
            ],
            temperature=0.1
        )

        # extract the content from the response
        content = response.choices[0].message.content.strip()

        # clean markdown
        
        content = re.sub(r"```json|```", "", content).strip()

        # parse the content as json
        result = json.loads(content)
       
        return validate_analysis(result)
    
    except json.JSONDecodeError:
            # LLM returned something unparseable
            # fall back to safe defaults
        return {
            "category": "Other",
            "priority": "Low",
            "summary": "Could not analyse email.",
            "action_items": [],
            "event_datetime": None,
            "duration_minutes": None,
            "location_or_link": None,
        }
    except Exception as e:
        return {
            "category": "Other",
            "priority": "Low",
            "summary": f"Error analyzing email: {str(e)}",
            "action_items": [],
            "event_datetime": None,
            "duration_minutes": None,
            "location_or_link": None,
        }
    
