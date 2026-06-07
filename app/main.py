import logging
import boto3
import watchtower
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager

from app.api.routes import router
from app.db.database import create_tables, check_db_connection
from app.scheduler import start_scheduler, stop_scheduler
from app.config import AWS_REGION, CLOUDWATCH_LOG_GROUP 

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)

# cloudwatch handler 
# CloudWatch handler — only attach if running on AWS (IAM role available).
# Local dev has no IAM role attached, so boto3 will fail to authenticate
# and we silently skip CloudWatch logging. The app still logs to stdout.
if AWS_REGION and CLOUDWATCH_LOG_GROUP:
    try:
        
        cw_handler = watchtower.CloudWatchLogHandler(
            log_group=CLOUDWATCH_LOG_GROUP,
            stream_name="inboxiq-app",
            boto3_client=boto3.client("logs", region_name=AWS_REGION)
        )
        cw_handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        ))
        logging.getLogger().addHandler(cw_handler)
        logger.info(f"[CloudWatch] Logs streaming to '{CLOUDWATCH_LOG_GROUP}' in {AWS_REGION}")
    except Exception as e:
        logger.warning(f"[CloudWatch] Failed to attach handler: {e}. Continuing with stdout only.")


limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    logger.info("[Startup] Starting Email Intelligence Agent...")
    if not check_db_connection():
        raise RuntimeError("Cannot connect to database. Check DATABASE_URL.")
    create_tables()
    start_scheduler()  # AFTER create_tables — first tick may touch the tables
    logger.info("[Startup] Ready.")
    yield
    # shutdown
    logger.info("[Shutdown] Shutting down.")
    stop_scheduler()

app = FastAPI(
    title="Email Intelligence Agent",
    description="AI-powered email analysis and automation platform",
    version="1.0.0",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.include_router(router)


# global exception handler — catches anything not handled in routes
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"[Global] Unhandled exception on {request.method} {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."}
    )


@app.get("/")
def root():
    return {
        "project": "Email Intelligence Agent",
        "status": "running",
        "version": "1.0.0"
    }


