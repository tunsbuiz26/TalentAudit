from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from talentaudit.adapters.db.base import Base
from talentaudit.adapters.db.session import get_db_session
from talentaudit.config import Settings
from talentaudit.main import create_app


class FakeDatabaseHealthChecker:
    def check(self) -> bool:
        return True


@pytest.fixture
def client() -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    def override_db_session() -> Iterator[Session]:
        with session_factory() as session:
            yield session

    app = create_app(
        Settings(environment="test"),
        FakeDatabaseHealthChecker(),
    )
    app.dependency_overrides[get_db_session] = override_db_session
    yield TestClient(app)
    app.dependency_overrides.clear()
    engine.dispose()


def test_create_and_get_job_policy(client: TestClient) -> None:
    payload = {
        "title": "AI/ML Engineer",
        "description": "Build machine learning services.",
        "requirements": [
            {"skill": "Python", "kind": "REQUIRED", "min_years": 2},
            {"skill": "Kubernetes", "kind": "PREFERRED"},
        ],
    }

    create_response = client.post("/api/v1/jobs", json=payload)

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["title"] == "AI/ML Engineer"
    assert created["status"] == "DRAFT"
    assert [item["skill"] for item in created["requirements"]] == [
        "python",
        "kubernetes",
    ]

    get_response = client.get(f"/api/v1/jobs/{created['id']}")

    assert get_response.status_code == 200
    assert get_response.json() == created


def test_get_unknown_job_returns_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/jobs/does-not-exist")

    assert response.status_code == 404


def test_create_job_rejects_empty_requirements(client: TestClient) -> None:
    response = client.post(
        "/api/v1/jobs",
        json={
            "title": "AI/ML Engineer",
            "description": "Build services.",
            "requirements": [],
        },
    )

    assert response.status_code == 422
