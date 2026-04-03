import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager

from app.api.routes import router
from app.db.database import create_tables, check_db_connection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    logger.info("[Startup] Starting Email Intelligence Agent...")
    if not check_db_connection():
        raise RuntimeError("Cannot connect to database. Check DATABASE_URL.")
    create_tables()
    logger.info("[Startup] Ready.")
    yield
    # shutdown
    logger.info("[Shutdown] Shutting down.")


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

# from fastapi import FastAPI
# from slowapi import Limiter, _rate_limit_exceeded_handler
# from slowapi.util import get_remote_address
# from slowapi.errors import RateLimitExceeded

# from app.api.routes import router
# from app.db.database import create_tables
# from contextlib import asynccontextmanager

# limiter = Limiter(key_func=get_remote_address)

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # startup
#     create_tables()
#     yield
#     # shutdown 

# app = FastAPI(
#     title = "Email Intelligence Agent",
#     description="AI-powered email analysis and automation platform",
#     version="1.0.0",
#     lifespan=lifespan
# )

# app.state.limiter = limiter# storing limiter inside app state so it can be accessed in routes globally
# app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)#instead of crashing return proper response http 429
# app.include_router(router) # connects actual api endpoints

# # health check endpoint - server running or no 
# @app.get("/")
# def root():
#     return {
#         "project": "Email intelligence agent",
#         "status": "running",
#         "version": "1.0.0"
#     }






