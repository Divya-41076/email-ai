import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError
from app.config import DATABASE_URL

logger = logging.getLogger(__name__)

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# dependency injection for the routes to get a db session
def get_db():
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"[DB] Session error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

# this is lazy creation of tables - they will be created o startup if they dont exist, but we avoid importing models ar the module level to prevent circular imports
def create_tables():
    try:
        import app.models.email_model
        Base.metadata.create_all(bind=engine)
        logger.info("[DB] Tables created successfully.")
    except SQLAlchemyError as e:
        logger.error(f"[DB] Failed to create tables: {str(e)}")
        raise #re-raise to prevent app from starting if we cant create the tables

# simple check to see if the DB is alive by exe a small query.
def check_db_connection():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("[DB] Connection check passed.")
        return True
    except SQLAlchemyError as e:
        logger.error(f"[DB] Connection check failed: {str(e)}")
        return False





