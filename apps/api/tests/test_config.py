from urllib.parse import urlsplit

import pytest
from nimbus_api.config import database_url
from psycopg.conninfo import conninfo_to_dict


def test_database_url_percent_encodes_each_connection_component() -> None:
    url = database_url(
        {
            "POSTGRES_USER": "nimbus@local",
            "POSTGRES_PASSWORD": "p@ss:/?#%",
            "POSTGRES_DB": "nimbus/project",
            "POSTGRES_HOST": "db.internal",
            "POSTGRES_PORT": "6543",
        }
    )

    parsed = urlsplit(url)
    connection_parts = conninfo_to_dict(url)

    assert parsed.scheme == "postgresql"
    assert parsed.hostname == "db.internal"
    assert parsed.port == 6543
    assert connection_parts["user"] == "nimbus@local"
    assert connection_parts["password"] == "p@ss:/?#%"
    assert connection_parts["dbname"] == "nimbus/project"


def test_database_url_normalizes_the_sqlalchemy_driver_prefix() -> None:
    assert database_url({"DATABASE_URL": "postgresql+psycopg://u:p@localhost/db"}) == (
        "postgresql://u:p@localhost/db"
    )


def test_postgres_components_are_canonical_over_a_stale_url() -> None:
    url = database_url(
        {
            "DATABASE_URL": "postgresql://old:stale@localhost/old",
            "POSTGRES_USER": "nimbus",
            "POSTGRES_PASSWORD": "new@password",
            "POSTGRES_DB": "nimbus",
        }
    )

    assert url == "postgresql://nimbus:new%40password@localhost:5432/nimbus"


def test_database_url_reports_missing_component_settings() -> None:
    with pytest.raises(RuntimeError, match="POSTGRES_PASSWORD"):
        database_url({"POSTGRES_USER": "nimbus", "POSTGRES_DB": "nimbus"})
