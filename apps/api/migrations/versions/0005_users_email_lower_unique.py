"""Enforce case-insensitive uniqueness for user email addresses."""

from alembic import op
from sqlalchemy import text

revision = "0005_users_email_lower_unique"
down_revision = "0004_chunk_flagged"
branch_labels = None
depends_on = None


def upgrade() -> None:
    duplicate = (
        op.get_bind()
        .execute(
            text(
                """
        SELECT lower(email), count(*)
        FROM users
        GROUP BY lower(email)
        HAVING count(*) > 1
        LIMIT 1
        """
            )
        )
        .first()
    )
    if duplicate:
        raise RuntimeError(
            "Cannot create users_email_lower_idx: users contains duplicate emails "
            "after case normalization. Resolve the duplicates, then rerun the migration."
        )
    op.execute("CREATE UNIQUE INDEX users_email_lower_idx ON users (lower(email))")


def downgrade() -> None:
    op.execute("DROP INDEX users_email_lower_idx")
