# InboxIQ — AI Email Intelligence Agent

> **Think less. Act faster. Your AI-powered inbox.**

An AI-powered backend system that autonomously fetches, analyzes, and automates Gmail inbox management using LLMs and cloud infrastructure.

---

## What It Does

InboxIQ connects to your Gmail, reads your emails, sends them through an AI pipeline, understands what each email is about, decides what to do with it, and stores everything in a PostgreSQL database — all accessible via a clean REST API.

```
Gmail Inbox
    ↓
Email Fetcher (Gmail API + OAuth)
    ↓
AI Analyzer (Groq — Llama 3.3 70B)
    ↓
Decision Engine (rule-based)
    ↓
Automation Service
    ↓
PostgreSQL (AWS RDS)
    ↓
FastAPI REST API
```

---

## Key Features

- **Real Gmail Integration** — OAuth 2.0 authentication with three-tier credential caching (valid token → silent refresh → full consent flow)
- **AI Email Analysis** — Groq Llama 3.3 70B extracts category, priority, summary, and action items from every email
- **Hybrid Priority Engine** — AI-assigned priority overridden by deterministic rules (important contacts, keyword detection)
- **2D Decision Matrix** — Category × Priority maps to specific automation actions
- **Async Processing** — FastAPI BackgroundTasks returns instant API responses while pipeline runs in background
- **Deduplication** — `gmail_message_id` ensures no email is ever processed twice
- **Rate Limiting** — SlowAPI per-IP rate limiting on all endpoints
- **Cloud Deployed** — Containerized FastAPI on AWS EC2 with PostgreSQL on RDS inside a custom VPC

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI + Uvicorn |
| Language | Python 3.11 |
| AI / LLM | Groq SDK — Llama 3.3 70B |
| Gmail Integration | Google API Python Client + google-auth-oauthlib |
| Database | PostgreSQL 17 |
| ORM | SQLAlchemy |
| Rate Limiting | SlowAPI |
| Containerization | Docker + Docker Compose |
| Cloud | AWS EC2 + RDS + VPC + CloudWatch + IAM |
| Cloud SDK | boto3 |
| Config | python-dotenv + Pydantic |

---

## System Architecture

```
User
 ↓
FastAPI (AWS EC2)          ← backend + rate limiting
 ↓
BackgroundTasks            ← async processing
 ↓
Gmail API                  ← fetch real emails
 ↓
Groq API (Llama 3.3 70B)  ← AI analysis
 ↓
Decision Engine            ← rule-based actions
 ↓
PostgreSQL (AWS RDS)       ← persistent storage
 ↓
CloudWatch                 ← logs + monitoring
```

### AWS Architecture

```
Internet
    ↓
Internet Gateway
    ↓
VPC (custom)
    ├── Public Subnet  → EC2 (FastAPI + Docker)
    └── Private Subnet → RDS (PostgreSQL)
```

RDS lives in a private subnet — never directly accessible from the internet.

---

## AI Pipeline

For every email, Groq returns structured JSON:

```json
{
  "category": "Job Opportunity",
  "priority": "High",
  "summary": "Recruiter from Google invited you for a backend engineer interview",
  "action_items": [
    "Confirm availability",
    "Prepare system design"
  ]
}
```

### Categories
`Job Opportunity` `Meeting` `Newsletter` `Notification` `Promotion` `Personal` `Spam` `Other`

### Priority Levels
`High` `Medium` `Low`

---

## Decision Engine

AI output feeds into a deterministic 2D matrix:

```
Category × Priority → Action
```

| Category | High | Medium | Low |
|---|---|---|---|
| Job Opportunity | mark_priority_and_notify | mark_priority | inbox |
| Meeting | extract_event_and_notify | extract_event | extract_event |
| Newsletter | inbox | archive | archive |
| Promotion | archive | archive | delete |
| Spam | delete | delete | delete |
| Personal | mark_priority | inbox | inbox |

### Priority Override Rules

```
Rule 1 → Sender in important contacts → force High
Rule 2 → High priority keywords in subject/body → force High
Rule 3 → Low priority keywords found → force Low
Rule 4 → Trust AI priority
```

AI is the analysis layer. Decision engine is the control layer. AI never directly controls the system.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | System status |
| GET | `/health` | Health check |
| POST | `/process-emails` | Fetch + analyze emails (async) |
| GET | `/emails` | Get all processed emails with analysis |
| GET | `/emails/{id}` | Get single email details |
| GET | `/stats` | System metrics + action breakdown |

### Example Response — `GET /emails`

```json
[
  {
    "id": 1,
    "subject": "Backend Engineer Interview Invitation",
    "sender": "recruiter@google.com",
    "received_at": "2024-04-01T10:30:00",
    "analysis": {
      "category": "Job Opportunity",
      "priority": "High",
      "summary": "Recruiter invited you for a backend engineer interview next Tuesday",
      "action_items": ["Confirm availability", "Prepare system design"],
      "action": "mark_priority_and_notify",
      "status": "done"
    }
  }
]
```

---

## Database Schema

```
emails
├── id (PK)
├── user_id
├── gmail_message_id (unique)
├── subject
├── sender
├── body
└── received_at

email_analysis
├── id (PK)
├── email_id (FK → emails)
├── category
├── priority
├── summary
├── action_items (JSONB)
├── automation_action
├── status
└── processed_at
```

`user_id` included from day one — schema is multi-user ready.

---

## Project Structure

```
email-ai/
│
├── app/
│   ├── main.py              ← FastAPI app + lifespan
│   ├── config.py            ← environment config
│   ├── scheduler.py         ← background scheduler
│   │
│   ├── api/
│   │   └── routes.py        ← all API endpoints
│   │
│   ├── services/
│   │   ├── email_fetcher.py ← Gmail API integration
│   │   ├── ai_analyzer.py   ← Groq AI pipeline
│   │   ├── decision_engine.py ← rule-based decisions
│   │   ├── automation_service.py ← action execution
│   │   └── pipeline.py      ← orchestrates everything
│   │
│   ├── db/
│   │   └── database.py      ← SQLAlchemy setup
│   │
│   ├── models/
│   │   └── email_model.py   ← DB + Pydantic models
│   │
│   └── utils/
│       ├── gmail_auth.py    ← OAuth credential handler
│       └── prompts.py       ← LLM prompt templates
│
├── .env                     ← environment variables
├── credentials.json         ← Gmail OAuth credentials
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .gitignore
```

---

## Local Setup

### Prerequisites
- Python 3.11+
- PostgreSQL
- Docker (optional)
- Groq API key — [console.groq.com](https://console.groq.com)
- Gmail OAuth credentials — [Google Cloud Console](https://console.cloud.google.com)

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/email-ai.git
cd email-ai
```

### 2. Create virtual environment

```bash
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Mac/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
```

Fill in your `.env`:

```env
GROQ_API_KEY=your_groq_api_key
DATABASE_URL=postgresql://postgres:password@localhost:5432/email_agent
GMAIL_CLIENT_ID=your_gmail_client_id
GMAIL_CLIENT_SECRET=your_gmail_client_secret
AWS_REGION=ap-south-1
CLOUDWATCH_LOG_GROUP=email-agent
```

### 5. Create database

```sql
CREATE DATABASE email_agent;
```

### 6. Run the server

```bash
uvicorn app.main:app --reload
```

### 7. Authenticate Gmail

Hit `POST /process-emails` — a browser window will open for Gmail OAuth. Login and grant permission. `token.pickle` will be saved automatically.

### 8. Open Swagger UI

```
http://localhost:8000/docs
```

---

## Docker Setup

```bash
docker-compose up --build
```

App runs on `http://localhost:8000`

---

## Environment Variables

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Groq API key for LLM calls |
| `DATABASE_URL` | PostgreSQL connection string |
| `GMAIL_CLIENT_ID` | Google OAuth client ID |
| `GMAIL_CLIENT_SECRET` | Google OAuth client secret |
| `AWS_REGION` | AWS region (default: ap-south-1) |
| `CLOUDWATCH_LOG_GROUP` | CloudWatch log group name |

---

## Security

- All secrets in `.env` — never hardcoded
- `credentials.json` and `token.pickle` excluded from git and Docker
- RDS in private subnet — no public internet access
- IAM roles for EC2 → CloudWatch access
- Gmail OAuth scopes minimal by default
- Rate limiting on all endpoints

---

## V2 Upgrade Path

| Feature | Technology |
|---|---|
| Async job queue | AWS SQS |
| Email attachments | AWS S3 |
| Public API | AWS API Gateway |
| Multi-user auth | JWT middleware |
| Caching | Redis (ElastiCache) |
| Load balancing | AWS ALB |
| Secret management | AWS Secrets Manager |
| Gmail automations | Labels + star + archive + draft replies |
| Concurrent processing | asyncio.gather |

---

## What This Project Demonstrates

| Domain | Skill |
|---|---|
| AI Engineering | Prompt engineering for structured JSON outputs, LLM response validation, fallback handling |
| Backend Architecture | Modular FastAPI design, async processing, rate limiting, error handling |
| System Design | Decision engine separation from AI layer, deduplication, schema design |
| Cloud Engineering | EC2 + RDS + VPC + CloudWatch + IAM on AWS |
| DevOps | Docker + Docker Compose containerization |
| Database Design | PostgreSQL with JSONB, foreign keys, multi-user ready schema |

---

## Author

**Divya** — Final year CSE student  
Building backend + cloud + AI systems

---

*Built with FastAPI, Groq, Gmail API, PostgreSQL, and AWS*
