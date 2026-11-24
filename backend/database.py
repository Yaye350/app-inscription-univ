import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

Base = declarative_base()

engine = None
SessionLocal = None


def init_engine(url: str | None = None):
    global engine, SessionLocal
    url = url or os.getenv("DATABASE_URL", "sqlite:///./inscriptions.db")
    connect_args = {}
    poolclass = None
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        if url in ("sqlite://", "sqlite:///:memory:"):
            poolclass = StaticPool
            url = "sqlite://"
    kwargs = {"connect_args": connect_args, "pool_pre_ping": not url.startswith("sqlite")}
    if poolclass is not None:
        kwargs["poolclass"] = poolclass
    engine = create_engine(url, **kwargs)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
