from fastapi.testclient import TestClient

from talentaudit.config import Settings
from talentaudit.main import create_app


class FakeDatabaseHealthChecker:
    def __init__(self, is_ready: bool) -> None:
        self.is_ready = is_ready

    def check(self) -> bool:
        return self.is_ready


def test_health_endpoint_does_not_require_database() -> None:
    client = TestClient(
        create_app(
            Settings(environment="test"),
            FakeDatabaseHealthChecker(is_ready=False),
        ),
    )

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "TalentAudit"}


def test_ready_endpoint_reports_database_up() -> None:
    client = TestClient(
        create_app(
            Settings(environment="test"),
            FakeDatabaseHealthChecker(is_ready=True),
        ),
    )

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "up"}


def test_ready_endpoint_fails_closed_when_database_is_down() -> None:
    client = TestClient(
        create_app(
            Settings(environment="test"),
            FakeDatabaseHealthChecker(is_ready=False),
        ),
    )

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "database": "down"}

