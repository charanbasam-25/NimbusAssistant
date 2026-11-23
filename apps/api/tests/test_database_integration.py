"""Database checks run separately from the fast, service-free unit suite."""

import psycopg
import pytest
from nimbus_api.config import database_url


@pytest.mark.integration
def test_pgvector_schema_is_ready_after_alembic_upgrade() -> None:
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
        migration = connection.execute("SELECT version_num FROM alembic_version").fetchone()

    assert extensions == {"vector", "pgcrypto"}
    assert user_region_nullable == (False,)
    assert migration == ("0003_user_region_required",)
