import json
import re
from groq import Groq
from app.config import GROQ_API_KEY
from app.utils.prompts import EMAIL_ANALYSIS_PROMPT

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
        "action_items": result.get("action_items", [])
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

    return validated



def analyze_email(subject:str,sender:str,body:str)->dict:
    # return type is dict with keys

    # build the prompt

    prompt = EMAIL_ANALYSIS_PROMPT.format(
        subject=subject,
        sender=sender,
        body=body
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
        return{
            "category":"other",
            "priority":"low",
            "summary":"Could not analyse email.",
            "action_items":[]
        }
    except Exception as e:
        return{
            "category":"other",
            "priority":"low",
            "summary":f"Error analyzing email: {str(e)}",
            "action_items":[]
        }
