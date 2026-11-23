"""Require an explicit home region for every user."""

from alembic import op

revision = "0003_user_region_required"
down_revision = "0002_chunk_provenance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE users ALTER COLUMN home_region SET NOT NULL")


def downgrade() -> None:
    op.execute("ALTER TABLE users ALTER COLUMN home_region DROP NOT NULL")
