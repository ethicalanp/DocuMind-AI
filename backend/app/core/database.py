from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATABASE_URL = f"sqlite:///{PROJECT_ROOT / 'documind.db'}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread":False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base=declarative_base()