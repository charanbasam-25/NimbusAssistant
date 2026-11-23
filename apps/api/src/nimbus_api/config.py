"""Shared environment and database connection configuration for Nimbus."""

import os
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
load_dotenv(REPOSITORY_ROOT / ".env")


def database_url(environ: Mapping[str, str] | None = None) -> str:
    """Return a psycopg-compatible URL, safely encoding URL components.

    The individual POSTGRES settings are canonical when all are available. A
    standalone ``DATABASE_URL`` is supported as an override for environments
    that do not provide those settings, and its credentials must be percent-
    encoded. Building from components safely handles characters like ``@`` and
    ``/`` in a password.
    """
    settings = os.environ if environ is None else environ
    required = ("POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB")
    if all(settings.get(key) for key in required):
        # Percent-encode each value independently; never interpolate raw credentials.
        user = quote(settings["POSTGRES_USER"], safe="")
        password = quote(settings["POSTGRES_PASSWORD"], safe="")
        database = quote(settings["POSTGRES_DB"], safe="")
        host = settings.get("POSTGRES_HOST", "localhost")
        port = settings.get("POSTGRES_PORT", "5432")
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"

    configured_url = settings.get("DATABASE_URL")
    if configured_url:
        return configured_url.replace("postgresql+psycopg://", "postgresql://", 1)

    missing = [key for key in required if not settings.get(key)]
    raise RuntimeError(f"Missing database settings: {', '.join(missing)}")
