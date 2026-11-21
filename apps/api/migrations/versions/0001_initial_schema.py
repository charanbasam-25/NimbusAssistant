"""Create Nimbus's initial security-aware schema."""
from alembic import op

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.execute("""
        CREATE TABLE users (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            email text NOT NULL UNIQUE,
            password_hash text NOT NULL,
            role text NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
            home_region text CHECK (home_region IN ('R1', 'R2')),
            created_at timestamptz NOT NULL DEFAULT now(),
            CHECK ((role = 'admin' AND home_region IS NOT NULL) OR role = 'user')
        )
    """)

    op.execute("""
        CREATE TABLE documents (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            source_url text NOT NULL,
            source_commit text NOT NULL,
            source_path text NOT NULL,
            title text NOT NULL,
            audience text NOT NULL CHECK (audience IN ('public', 'internal')),
            region text NOT NULL CHECK (region IN ('global', 'R1', 'R2')),
            content_hash text NOT NULL,
            metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
            created_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE (source_commit, source_path, content_hash)
        )
    """)

    op.execute("""
        CREATE TABLE chunks (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            ordinal integer NOT NULL CHECK (ordinal >= 0),
            heading text,
            content text NOT NULL,
            embedding vector(384),
            search_text tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
            token_count integer NOT NULL CHECK (token_count > 0),
            created_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE (document_id, ordinal)
        )
    """)
    op.execute("CREATE INDEX chunks_search_text_idx ON chunks USING gin (search_text)")
    op.execute("CREATE INDEX chunks_embedding_idx ON chunks USING hnsw (embedding vector_cosine_ops)")
    op.execute("CREATE INDEX documents_access_idx ON documents (audience, region)")

    op.execute("""
        CREATE TABLE tickets (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id uuid NOT NULL REFERENCES users(id),
            region text NOT NULL CHECK (region IN ('R1', 'R2')),
            subject text NOT NULL,
            category text NOT NULL CHECK (category IN ('bug', 'how-to', 'access', 'billing', 'feature', 'security', 'other')),
            body text NOT NULL,
            status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'submitted', 'open', 'closed')),
            created_at timestamptz NOT NULL DEFAULT now(),
            submitted_at timestamptz
        )
    """)

    op.execute("""
        CREATE TABLE query_log (
            id bigserial PRIMARY KEY,
            request_id uuid NOT NULL,
            user_id uuid REFERENCES users(id),
            persona text NOT NULL CHECK (persona IN ('guest', 'R1', 'R2')),
            route text NOT NULL,
            outcome text NOT NULL,
            latency_ms integer,
            first_token_ms integer,
            llm_input_tokens integer,
            llm_output_tokens integer,
            created_at timestamptz NOT NULL DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE events (
            id bigserial PRIMARY KEY,
            request_id uuid NOT NULL,
            event_type text NOT NULL,
            severity text NOT NULL DEFAULT 'info' CHECK (severity IN ('info', 'warning', 'critical')),
            timings jsonb NOT NULL DEFAULT '{}'::jsonb,
            attributes jsonb NOT NULL DEFAULT '{}'::jsonb,
            created_at timestamptz NOT NULL DEFAULT now()
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS events")
    op.execute("DROP TABLE IF EXISTS query_log")
    op.execute("DROP TABLE IF EXISTS tickets")
    op.execute("DROP TABLE IF EXISTS chunks")
    op.execute("DROP TABLE IF EXISTS documents")
    op.execute("DROP TABLE IF EXISTS users")
