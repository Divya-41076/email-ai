from dotenv import load_dotenv
import os

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID") #identitfies my app to google oauth
GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET")

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
CLOUDWATCH_LOG_GROUP = os.getenv("CLOUDWATCH_LOG_GROUP", "email-agent")

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

SCHEDULER_INTERVAL_MINUTES = int(os.getenv("SCHEDULER_INTERVAL_MINUTES", "5"))
