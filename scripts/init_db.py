"""GRC Platform - Database Initialization Script.

Creates all required database tables for the GRC Platform MVP.

Tables:
    - frameworks: Compliance frameworks (e.g., NIST SP 800-53)
    - controls: Security controls within frameworks
    - evidence_artifacts: Uploaded evidence documents
    - evidence_control_mappings: Links evidence to controls
    - review_workflows: Approve/reject workflows for evidence
    - audit_logs: Immutable audit trail
    - users: System users
    - agent_sessions: AI agent conversation sessions
    - knowledge_base: Compliance knowledge for RAG

Run with:
    python scripts/init_db.py
"""

import os
import uuid
from typing import Any, Optional

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

# Schema SQL definitions
CREATE_EXTENSIONS_SQL = """
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
"""

CREATE_TABLES_SQL = """

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Compliance Frameworks
CREATE TABLE IF NOT EXISTS frameworks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Controls within frameworks
CREATE TABLE IF NOT EXISTS controls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    framework_id UUID REFERENCES frameworks(id) ON DELETE CASCADE,
    control_id VARCHAR(100) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    control_family VARCHAR(100),
    priority VARCHAR(50) DEFAULT 'medium',
    artifact_requirements JSONB DEFAULT '[]'::jsonb,
    cross_framework_mappings JSONB DEFAULT '{}'::jsonb,
    UNIQUE(framework_id, control_id)
);

-- Evidence artifacts (uploaded documents)
CREATE TABLE IF NOT EXISTS evidence_artifacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    file_path VARCHAR(1000),
    file_type VARCHAR(50),
    file_size BIGINT,
    checksum VARCHAR(64),
    content_text TEXT,
    embedding_vector VECTOR(1024),
    uploaded_by UUID REFERENCES users(id),
    uploaded_at TIMESTAMP DEFAULT NOW()
);

-- Evidence-to-control mappings
CREATE TABLE IF NOT EXISTS evidence_control_mappings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    evidence_id UUID REFERENCES evidence_artifacts(id) ON DELETE CASCADE,
    control_id UUID REFERENCES controls(id) ON DELETE CASCADE,
    weightage DECIMAL(5,2),
    artifact_type VARCHAR(100),
    mapping_status VARCHAR(50) DEFAULT 'pending',
    mapped_at TIMESTAMP DEFAULT NOW()
);

-- Review workflows
CREATE TABLE IF NOT EXISTS review_workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(50),
    entity_id UUID,
    workflow_status VARCHAR(50) DEFAULT 'pending',
    submitted_by UUID REFERENCES users(id),
    reviewed_by UUID REFERENCES users(id),
    review_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Immutable audit logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100),
    entity_type VARCHAR(50),
    entity_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT NOW()
);

-- AI agent conversation sessions
CREATE TABLE IF NOT EXISTS agent_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    session_type VARCHAR(50),
    context JSONB,
    memory_summary TEXT,
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP
);

-- RAG knowledge base (compliance documents for vector search)
CREATE TABLE IF NOT EXISTS knowledge_base (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500),
    content TEXT,
    source VARCHAR(255),
    chunk_index INTEGER,
    embedding_vector VECTOR(1024),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);
"""

CREATE_INDEXES_SQL = """
CREATE INDEX IF NOT EXISTS idx_controls_framework_id ON controls(framework_id);
CREATE INDEX IF NOT EXISTS idx_controls_control_family ON controls(control_family);
CREATE INDEX IF NOT EXISTS idx_evidence_control_mappings_evidence_id ON evidence_control_mappings(evidence_id);
CREATE INDEX IF NOT EXISTS idx_evidence_control_mappings_control_id ON evidence_control_mappings(control_id);
CREATE INDEX IF NOT EXISTS idx_review_workflows_status ON review_workflows(workflow_status);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_user_id ON agent_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_source ON knowledge_base(source);
"""


def get_connection() -> Any:
    """Create a database connection using the DATABASE_URL environment variable.

    Returns:
        connection: psycopg2 connection object.

    Raises:
        Exception: If connection fails.
    """
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://grc_user:grc_pass@localhost:5432/grc_dev",
    )
    conn = psycopg2.connect(database_url)
    conn.autocommit = True
    return conn


def init_database(conn: Any) -> None:
    """Create all database tables and extensions.

    All operations are idempotent (IF NOT EXISTS).

    Args:
        conn: Database connection object.
    """
    with conn.cursor() as cur:
        print("Creating extensions...")
        cur.execute(CREATE_EXTENSIONS_SQL)
        print("  ✓ uuid-ossp and vector extensions created")

        print("Creating tables...")
        cur.execute(CREATE_TABLES_SQL)
        print("  ✓ All tables created successfully")

        print("Creating indexes...")
        cur.execute(CREATE_INDEXES_SQL)
        print("  ✓ All indexes created successfully")

    print("\nDatabase initialization complete!")


def verify_tables(conn: Any) -> list[dict[str, Any]]:
    """Verify that all expected tables exist.

    Args:
        conn: Database connection object.

    Returns:
        List of table information dictionaries.
    """
    expected_tables = [
        "users",
        "frameworks",
        "controls",
        "evidence_artifacts",
        "evidence_control_mappings",
        "review_workflows",
        "audit_logs",
        "agent_sessions",
        "knowledge_base",
    ]

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' "
            "ORDER BY table_name"
        )
        existing_tables = [row["table_name"] for row in cur.fetchall()]

    results = []
    for table in expected_tables:
        exists = table in existing_tables
        results.append({"table": table, "exists": exists})
        status = "✓" if exists else "✗"
        print(f"  {status} {table}")

    return results


def main() -> None:
    """Main entry point for database initialization."""
    print("=" * 50)
    print("  GRC Platform - Database Initialization")
    print("=" * 50)

    try:
        conn = get_connection()
        print(f"\nConnected to database successfully.\n")

        init_database(conn)

        print("\nVerifying tables...")
        tables = verify_tables(conn)

        all_exist = all(t["exists"] for t in tables)
        if all_exist:
            print("\n✅ All 9 tables created successfully!")
        else:
            missing = [t["table"] for t in tables if not t["exists"]]
            print(f"\n⚠️  Missing tables: {', '.join(missing)}")

        conn.close()

    except Exception as e:
        print(f"\n❌ Database initialization failed: {e}")
        raise


if __name__ == "__main__":
    main()
