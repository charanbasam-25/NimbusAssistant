"""Database checks run separately from the fast, service-free unit suite."""

from pathlib import Path

import psycopg
import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from nimbus_api.config import database_url

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.integration
def test_pgvector_schema_is_ready_after_alembic_upgrade() -> None:
    alembic_config = Config(str(ROOT / "apps" / "api" / "alembic.ini"))
    alembic_config.set_main_option("script_location", str(ROOT / "apps" / "api" / "migrations"))
    expected_head = ScriptDirectory.from_config(alembic_config).get_current_head()
    with psycopg.connect(database_url()) as connection:
        extensions = {
            row[0]
            for row in connection.execute(
                "SELECT extname FROM pg_extension WHERE extname = ANY(%s)",
                (["vector", "pgcrypto"],),
            )
        }
        user_region_nullable = connection.execute(
            """
            SELECT is_nullable = 'YES'
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'users'
              AND column_name = 'home_region'
            """
        ).fetchone()
        flagged_column = connection.execute(
            """
            SELECT is_nullable = 'NO' AND column_default IN ('false', 'false::boolean')
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'chunks' AND column_name = 'flagged'
            """
        ).fetchone()
        migration = connection.execute("SELECT version_num FROM alembic_version").fetchone()
        email_index = connection.execute(
            "SELECT indexdef FROM pg_indexes WHERE indexname = 'users_email_lower_idx'"
        ).fetchone()

    assert extensions == {"vector", "pgcrypto"}
    assert user_region_nullable == (False,)
    assert flagged_column == (True,)
    assert migration == (expected_head,)
    assert email_index is not None
    assert "UNIQUE INDEX users_email_lower_idx" in email_index[0]
    assert "lower(email)" in email_index[0]
