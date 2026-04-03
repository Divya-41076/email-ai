# from sqlalchemy import create_engine
# from app.config import DATABASE_URL # DB connection string from evn
# from sqlalchemy.orm import sessionmaker # used to create DB sessions
# from sqlalchemy.ext.declarative import declarative_base # used to define ORM models - tables in db

# engine = create_engine(DATABASE_URL) # this creates a db conn = entry point to the db

# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) # factory for creating db sessions and connect session to db

# Base = declarative_base() #all your models will inherit from this

# def get_db(): #fastapi dependency to get db session for each request and close it after
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# def create_tables():
#     import app.models.email_model
#     Base.metadata.create_all(bind=engine)

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


def create_tables():
    try:
        import app.models.email_model
        Base.metadata.create_all(bind=engine)
        logger.info("[DB] Tables created successfully.")
    except SQLAlchemyError as e:
        logger.error(f"[DB] Failed to create tables: {str(e)}")
        raise


def check_db_connection():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("[DB] Connection check passed.")
        return True
    except SQLAlchemyError as e:
        logger.error(f"[DB] Connection check failed: {str(e)}")
        return False





