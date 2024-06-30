from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

USER = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")
HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}/{DB_NAME}"
engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(
    autoflush=False, autocommit=False, bind=engine
)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()
