"""Run real Alembic revisions against a fresh disposable SQL database."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


def test_upgrade_preserves_documents_and_downgrade_restores_columns(
    monkeypatch,
) -> None:
    def forbid_default_database(*args, **kwargs):
        raise AssertionError(
            "Migration tests must use the injected disposable connection"
        )

    monkeypatch.setattr("sqlalchemy.engine_from_config", forbid_default_database)
    root = Path(__file__).parents[2]
    configuration = Config(str(root / "alembic.ini"))
    configuration.set_main_option("script_location", str(root / "migrations"))
    engine = create_engine("sqlite://")
    with engine.connect() as connection:
        configuration.attributes["connection"] = connection
        command.upgrade(configuration, "0002_documents")
        connection.execute(
            text(
                "INSERT INTO documents "
                "(id,storage_key,sha256,mime_type,size_bytes,created_at) "
                "VALUES ('synthetic','generated.txt',:hash,'text/plain',"
                "12,CURRENT_TIMESTAMP)"
            ),
            {"hash": "a" * 64},
        )
        connection.commit()
        command.upgrade(configuration, "head")
        assert (
            connection.execute(text("SELECT parser_status FROM documents")).scalar_one()
            == "PENDING"
        )
        assert "page_count" in {
            c["name"] for c in inspect(connection).get_columns("documents")
        }
        connection.commit()
        command.downgrade(configuration, "0002_documents")
        assert "page_count" not in {
            c["name"] for c in inspect(connection).get_columns("documents")
        }
        assert (
            connection.execute(text("SELECT count(*) FROM documents")).scalar_one() == 1
        )
    engine.dispose()
