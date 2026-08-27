import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_alumni_tracker.db")


@pytest.fixture()
def db_session_factory():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    from app.infrastructure.db import Base

    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    yield TestingSessionLocal

    engine.dispose()
    os.remove(path)


@pytest.fixture()
def create_user(db_session_factory):
    def _create_user(name="Darma", email="darma@test.com", password="secret123"):
        from app.services.auth_service import AuthService

        with db_session_factory() as db:
            return AuthService(db).register(name, email, password)

    return _create_user


@pytest.fixture()
def client(db_session_factory):
    from app.infrastructure.db import get_db
    from app.main import app

    def override_get_db():
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
@pytest.fixture()
def auth_headers(client, create_user):
    create_user()
    res = client.post(
        "/api/v1/auth/login", json={"email": "darma@test.com", "password": "secret123"}
    )
    token = res.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
