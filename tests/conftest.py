import os

os.environ["SECRET_KEY"] = "test-secret-key-for-pytest-only-0123456789"
os.environ["DATABASE_URL"] = "sqlite://"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.services import fcm


@pytest.fixture()
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    def override():
        with Session() as s:
            yield s

    app.dependency_overrides[get_db] = override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def fake_fcm(monkeypatch):
    """Replace real FCM with a recorder."""
    calls = []

    def fake_send(tokens, title, body, data):
        calls.append({"tokens": tokens, "title": title, "body": body, "data": data})
        return [fcm.SendResult(t, message_id=f"projects/x/messages/{i}") for i, t in enumerate(tokens)]

    monkeypatch.setattr(fcm, "send_to_tokens", fake_send)
    return calls


TOKEN_A = "a" * 40
EMAIL, PASSWORD = "alice@example.com", "s3cretpass"


@pytest.fixture()
def auth(client):
    client.post("/auth/register", json={"email": EMAIL, "password": PASSWORD})
    r = client.post("/auth/login", data={"username": EMAIL, "password": PASSWORD})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
