"""Mark chunks that contain injection or unsafe-URL instructions."""

from alembic import op

revision = "0004_chunk_flagged"
down_revision = "0003_user_region_required"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE chunks ADD COLUMN flagged boolean NOT NULL DEFAULT false")


def downgrade() -> None:
    op.execute("ALTER TABLE chunks DROP COLUMN flagged")
