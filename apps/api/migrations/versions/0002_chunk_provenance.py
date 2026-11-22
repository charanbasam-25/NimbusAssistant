"""Track exactly what produced each searchable chunk."""

from alembic import op

revision = "0002_chunk_provenance"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Preserve the literal chunk text separately from the context-enriched embedding input.
    op.execute("ALTER TABLE chunks ADD COLUMN embedding_input text")
    op.execute("ALTER TABLE chunks ADD COLUMN content_hash text")
    # NULL means no vector has been generated yet; once embedded, record its exact model spec.
    op.execute("ALTER TABLE chunks ADD COLUMN embedding_spec jsonb")
    op.execute("ALTER TABLE chunks ADD COLUMN processing jsonb NOT NULL DEFAULT '{}'::jsonb")

    # Backfill existing rows so the migration works for already-ingested documents too.
    op.execute("""
        UPDATE chunks AS c
        SET embedding_input = concat_ws(' / ', NULLIF(d.title, ''), NULLIF(c.heading, ''))
                              || ': ' || c.content,
            content_hash = 'sha256:' || encode(digest(convert_to(c.content, 'UTF8'), 'sha256'), 'hex'),
            processing = '{"parser_version":"markdown-structure-v1",'
                         '"chunker_version":"heading-paragraph-600-token-v1"}'::jsonb
        FROM documents AS d
        WHERE d.id = c.document_id
    """)
    op.execute("ALTER TABLE chunks ALTER COLUMN embedding_input SET NOT NULL")
    op.execute("ALTER TABLE chunks ALTER COLUMN content_hash SET NOT NULL")


def downgrade() -> None:
    op.execute("ALTER TABLE chunks DROP COLUMN processing")
    op.execute("ALTER TABLE chunks DROP COLUMN embedding_spec")
    op.execute("ALTER TABLE chunks DROP COLUMN content_hash")
    op.execute("ALTER TABLE chunks DROP COLUMN embedding_input")
