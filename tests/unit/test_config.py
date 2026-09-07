import pytest
from pydantic import ValidationError

from talentaudit.config import Settings


def test_settings_use_safe_local_defaults() -> None:
    settings = Settings(environment="test")

    assert settings.environment == "test"
    assert settings.database_url.startswith("postgresql+")
    assert settings.db_connect_timeout_seconds == 3


def test_settings_reject_non_postgresql_database_url() -> None:
    with pytest.raises(ValidationError):
        Settings(environment="test", database_url="sqlite:///local.db")
