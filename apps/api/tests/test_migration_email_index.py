import importlib.util
from pathlib import Path

import pytest

MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "0005_users_email_lower_unique.py"
)


class FakeResult:
    def __init__(self, row):
        self.row = row

    def first(self):
        return self.row


class FakeOperations:
    def __init__(self, duplicate):
        self.duplicate = duplicate
        self.executed = []
        self.connection = self

    def get_bind(self):
        return self.connection

    def execute(self, statement):
        if "GROUP BY lower(email)" in str(statement):
            return FakeResult(self.duplicate)
        self.executed.append(statement)


def _load_migration(operations):
    spec = importlib.util.spec_from_file_location("migration_0005", MIGRATION_PATH)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    migration.op = operations
    return migration


def test_email_index_migration_rejects_duplicates_with_clear_error() -> None:
    operations = FakeOperations(("duplicate@example.test", 2))
    migration = _load_migration(operations)

    with pytest.raises(RuntimeError, match="duplicate emails after case normalization"):
        migration.upgrade()

    assert operations.executed == []


def test_email_index_migration_creates_expression_unique_index() -> None:
    operations = FakeOperations(None)
    migration = _load_migration(operations)

    migration.upgrade()

    assert operations.executed == [
        "CREATE UNIQUE INDEX users_email_lower_idx ON users (lower(email))"
    ]
