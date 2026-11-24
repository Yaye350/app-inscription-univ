import os
import tempfile

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp()
os.environ["SECRET_KEY"] = "test-secret-key-for-local-tests-only"
os.environ["SEED"] = "0"

import pytest
from fastapi.testclient import TestClient

import database
from main import app


@pytest.fixture
def client():
    database.Base.metadata.drop_all(bind=database.engine)
    database.Base.metadata.create_all(bind=database.engine)
    with TestClient(app) as test_client:
        yield test_client
    database.Base.metadata.drop_all(bind=database.engine)


@pytest.fixture
def db():
    database.Base.metadata.create_all(bind=database.engine)
    session = database.SessionLocal()
    try:
        yield session
    finally:
        session.close()
