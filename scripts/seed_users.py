#!/usr/bin/env python3
"""Create or update the three synthetic Nimbus access-evaluation users."""

from __future__ import annotations

import os
import sys

import psycopg
from nimbus_api.auth import hash_password
from nimbus_api.config import database_url

USERS = (
    ("r1-user@nimbus.test", "user", "R1"),
    ("r2-user@nimbus.test", "user", "R2"),
    ("admin-r1@nimbus.test", "admin", "R1"),
)


def main() -> int:
    password = os.environ.get("SEED_PASSWORD", "")
    if len(password) < 12:
        print("SEED_PASSWORD must contain at least 12 characters.", file=sys.stderr)
        return 2

    with psycopg.connect(database_url()) as connection, connection.transaction():
        for email, role, region in USERS:
            connection.execute(
                """
                INSERT INTO users (email, password_hash, role, home_region)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (email) DO UPDATE
                SET password_hash = EXCLUDED.password_hash,
                    role = EXCLUDED.role,
                    home_region = EXCLUDED.home_region
                """,
                (email, hash_password(password), role, region),
            )
    print(f"Seeded or updated {len(USERS)} synthetic Nimbus users.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
