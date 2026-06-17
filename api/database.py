"""GRC Platform - Database Connection Layer.

Provides connection pooling for PostgreSQL + pgvector and CRUD helper functions.
Uses psycopg2's ThreadedConnectionPool for thread-safe connection management.
"""

import hashlib
import os
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Generator, Optional

import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor, RealDictRow
from psycopg2.pool import ThreadedConnectionPool

from config import get_config

config = get_config()

# Global connection pool singleton
_pool: Optional[ThreadedConnectionPool] = None


def get_pool() -> ThreadedConnectionPool:
    """Get or create the database connection pool.

    Returns:
        ThreadedConnectionPool: The global connection pool instance.

    Raises:
        RuntimeError: If database URL is not configured.
    """
    global _pool

    if _pool is not None:
        return _pool

    database_url = config.database.url
    if not database_url or "postgresql" not in database_url:
        raise RuntimeError(
            "Database URL not configured. Set DATABASE_URL in .env file."
        )

    _pool = ThreadedConnectionPool(
        minconn=config.database.pool_min,
        maxconn=config.database.pool_max,
        dsn=database_url,
    )
    return _pool


def close_pool() -> None:
    """Close the global connection pool if it exists."""
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None


@contextmanager
def get_connection() -> Generator[Any, None, None]:
    """Get a connection from the pool.

    Yields:
        psycopg2 connection object.

    Raises:
        RuntimeError: If pool is not initialized.
    """
    pool = get_pool()
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


@contextmanager
def get_cursor() -> Generator[Any, None, None]:
    """Get a cursor from a pooled connection.

    Yields:
        psycopg2 cursor with RealDictCursor factory.
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur


# =============================================================================
# Audit Logging
# =============================================================================

_AUDIT_INSERT_SQL = """
    INSERT INTO audit_logs (id, user_id, action, entity_type, entity_id,
                            old_values, new_values, ip_address, created_at)
    VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s)
"""


def create_audit_log(
    action: str,
    entity_type: str,
    entity_id: str,
    user_id: Optional[str] = None,
    old_values: Optional[dict[str, Any]] = None,
    new_values: Optional[dict[str, Any]] = None,
    ip_address: Optional[str] = None,
) -> dict[str, Any]:
    """Create an audit log entry.

    Args:
        action: The action performed (e.g., 'CREATE_EVIDENCE', 'MAP_EVIDENCE').
        entity_type: The type of entity affected.
        entity_id: The ID of the entity affected.
        user_id: Optional user ID who performed the action.
        old_values: Optional previous state of the entity.
        new_values: Optional new state of the entity.
        ip_address: Optional IP address of the requester.

    Returns:
        dict: The created audit log entry.
    """
    log_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    with get_cursor() as cur:
        cur.execute(
            _AUDIT_INSERT_SQL,
            (
                log_id,
                user_id,
                action,
                entity_type,
                entity_id,
                json_dumps(old_values) if old_values else None,
                json_dumps(new_values) if new_values else None,
                ip_address,
                now,
            ),
        )

    return {
        "id": log_id,
        "user_id": user_id,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "old_values": old_values,
        "new_values": new_values,
        "ip_address": ip_address,
        "created_at": now.isoformat(),
    }


# =============================================================================
# Framework CRUD
# =============================================================================

_FRAMEWORK_INSERT_SQL = """
    INSERT INTO frameworks (id, name, version, description, created_at)
    VALUES (%s, %s, %s, %s, %s)
"""

_FRAMEWORK_SELECT_ALL_SQL = """
    SELECT id, name, version, description, created_at
    FROM frameworks
    ORDER BY name
"""

_FRAMEWORK_SELECT_BY_ID_SQL = """
    SELECT id, name, version, description, created_at
    FROM frameworks
    WHERE id = %s
"""


def list_frameworks() -> list[dict[str, Any]]:
    """List all compliance frameworks.

    Returns:
        list[dict]: List of framework records.
    """
    with get_cursor() as cur:
        cur.execute(_FRAMEWORK_SELECT_ALL_SQL)
        rows = cur.fetchall()
    return [_row_to_dict(r) for r in rows]


def get_framework(framework_id: str) -> Optional[dict[str, Any]]:
    """Get a single framework by ID.

    Args:
        framework_id: UUID of the framework.

    Returns:
        Optional[dict]: Framework record or None if not found.
    """
    with get_cursor() as cur:
        cur.execute(_FRAMEWORK_SELECT_BY_ID_SQL, (framework_id,))
        row = cur.fetchone()
    return _row_to_dict(row) if row else None


def create_framework(
    name: str,
    version: Optional[str] = None,
    description: Optional[str] = None,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> dict[str, Any]:
    """Create a new framework.

    Args:
        name: Framework name.
        version: Optional version string.
        description: Optional description.
        user_id: Optional user ID for audit.
        ip_address: Optional IP for audit.

    Returns:
        dict: Created framework record.
    """
    framework_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    with get_cursor() as cur:
        cur.execute(
            _FRAMEWORK_INSERT_SQL,
            (framework_id, name, version, description, now),
        )

    new_values = {"id": framework_id, "name": name, "version": version, "description": description}
    create_audit_log(
        action="CREATE_FRAMEWORK",
        entity_type="framework",
        entity_id=framework_id,
        user_id=user_id,
        new_values=new_values,
        ip_address=ip_address,
    )

    return {
        "id": framework_id,
        "name": name,
        "version": version,
        "description": description,
        "created_at": now.isoformat(),
    }


# =============================================================================
# Control CRUD
# =============================================================================

_CONTROLS_SELECT_BY_FRAMEWORK_SQL = """
    SELECT id, framework_id, control_id, title, description,
           control_family, priority, artifact_requirements,
           cross_framework_mappings
    FROM controls
    WHERE framework_id = %s
    ORDER BY control_id
"""

_CONTROL_SELECT_BY_ID_SQL = """
    SELECT id, framework_id, control_id, title, description,
           control_family, priority, artifact_requirements,
           cross_framework_mappings
    FROM controls
    WHERE id = %s
"""


def list_controls_by_framework(framework_id: str) -> list[dict[str, Any]]:
    """List all controls for a given framework.

    Args:
        framework_id: UUID of the framework.

    Returns:
        list[dict]: List of control records.
    """
    with get_cursor() as cur:
        cur.execute(_CONTROLS_SELECT_BY_FRAMEWORK_SQL, (framework_id,))
        rows = cur.fetchall()
    return [_row_to_dict(r) for r in rows]


def get_control(control_id: str) -> Optional[dict[str, Any]]:
    """Get a single control by ID.

    Args:
        control_id: UUID of the control.

    Returns:
        Optional[dict]: Control record or None if not found.
    """
    with get_cursor() as cur:
        cur.execute(_CONTROL_SELECT_BY_ID_SQL, (control_id,))
        row = cur.fetchone()
    return _row_to_dict(row) if row else None


# =============================================================================
# Evidence CRUD
# =============================================================================

_EVIDENCE_INSERT_SQL = """
    INSERT INTO evidence_artifacts (id, name, file_path, file_type, file_size,
                                    checksum, content_text, uploaded_by, uploaded_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

_EVIDENCE_SELECT_ALL_SQL = """
    SELECT id, name, file_path, file_type, file_size, checksum,
           content_text, uploaded_by, uploaded_at
    FROM evidence_artifacts
    ORDER BY uploaded_at DESC
"""

_EVIDENCE_SELECT_BY_ID_SQL = """
    SELECT id, name, file_path, file_type, file_size, checksum,
           content_text, uploaded_by, uploaded_at
    FROM evidence_artifacts
    WHERE id = %s
"""


def list_evidence() -> list[dict[str, Any]]:
    """List all evidence artifacts.

    Returns:
        list[dict]: List of evidence records.
    """
    with get_cursor() as cur:
        cur.execute(_EVIDENCE_SELECT_ALL_SQL)
        rows = cur.fetchall()
    return [_row_to_dict(r) for r in rows]


def get_evidence(evidence_id: str) -> Optional[dict[str, Any]]:
    """Get a single evidence artifact by ID.

    Args:
        evidence_id: UUID of the evidence artifact.

    Returns:
        Optional[dict]: Evidence record or None if not found.
    """
    with get_cursor() as cur:
        cur.execute(_EVIDENCE_SELECT_BY_ID_SQL, (evidence_id,))
        row = cur.fetchone()
    return _row_to_dict(row) if row else None


def create_evidence(
    name: str,
    file_path: str,
    file_type: str,
    file_size: Optional[int] = None,
    checksum: Optional[str] = None,
    content_text: Optional[str] = None,
    uploaded_by: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> dict[str, Any]:
    """Create a new evidence artifact record.

    Args:
        name: Original filename.
        file_path: Path to stored file.
        file_type: File extension/MIME type.
        file_size: Optional file size in bytes.
        checksum: Optional file checksum.
        content_text: Optional extracted text content.
        uploaded_by: Optional user ID.
        ip_address: Optional IP for audit.

    Returns:
        dict: Created evidence artifact record.
    """
    evidence_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    with get_cursor() as cur:
        cur.execute(
            _EVIDENCE_INSERT_SQL,
            (
                evidence_id,
                name,
                file_path,
                file_type,
                file_size,
                checksum,
                content_text,
                uploaded_by,
                now,
            ),
        )

    new_values = {
        "id": evidence_id,
        "name": name,
        "file_path": file_path,
        "file_type": file_type,
        "file_size": file_size,
        "checksum": checksum,
        "uploaded_by": uploaded_by,
    }
    create_audit_log(
        action="CREATE_EVIDENCE",
        entity_type="evidence_artifact",
        entity_id=evidence_id,
        user_id=uploaded_by,
        new_values=new_values,
        ip_address=ip_address,
    )

    return {
        "id": evidence_id,
        "name": name,
        "file_path": file_path,
        "file_type": file_type,
        "file_size": file_size,
        "checksum": checksum,
        "content_text": content_text,
        "uploaded_by": uploaded_by,
        "uploaded_at": now.isoformat(),
    }


# =============================================================================
# Evidence-Control Mapping CRUD
# =============================================================================

_MAPPING_INSERT_SQL = """
    INSERT INTO evidence_control_mappings
        (id, evidence_id, control_id, weightage, artifact_type, mapping_status, mapped_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
"""

_MAPPING_SELECT_BY_EVIDENCE_SQL = """
    SELECT ecm.id, ecm.evidence_id, ecm.control_id, ecm.weightage,
           ecm.artifact_type, ecm.mapping_status, ecm.mapped_at,
           c.control_id AS control_ref_id, c.title AS control_title
    FROM evidence_control_mappings ecm
    JOIN controls c ON c.id = ecm.control_id
    WHERE ecm.evidence_id = %s
    ORDER BY ecm.mapped_at DESC
"""

_MAPPING_SELECT_BY_CONTROL_SQL = """
    SELECT ecm.id, ecm.evidence_id, ecm.control_id, ecm.weightage,
           ecm.artifact_type, ecm.mapping_status, ecm.mapped_at,
           ea.name AS evidence_name, ea.file_type
    FROM evidence_control_mappings ecm
    JOIN evidence_artifacts ea ON ea.id = ecm.evidence_id
    WHERE ecm.control_id = %s
    ORDER BY ecm.mapped_at DESC
"""

_MAPPING_SELECT_BY_ID_SQL = """
    SELECT id, evidence_id, control_id, weightage, artifact_type,
           mapping_status, mapped_at
    FROM evidence_control_mappings
    WHERE id = %s
"""

_MAPPING_UPDATE_STATUS_SQL = """
    UPDATE evidence_control_mappings
    SET mapping_status = %s
    WHERE id = %s
    RETURNING id, evidence_id, control_id, weightage, artifact_type, mapping_status, mapped_at
"""


def create_mapping(
    evidence_id: str,
    control_id: str,
    weightage: float,
    artifact_type: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> dict[str, Any]:
    """Create an evidence-to-control mapping.

    Args:
        evidence_id: UUID of the evidence artifact.
        control_id: UUID of the control.
        weightage: Weightage percentage for this mapping.
        artifact_type: The artifact type being mapped.
        user_id: Optional user ID for audit.
        ip_address: Optional IP for audit.

    Returns:
        dict: Created mapping record.
    """
    mapping_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    with get_cursor() as cur:
        cur.execute(
            _MAPPING_INSERT_SQL,
            (mapping_id, evidence_id, control_id, weightage, artifact_type, "pending", now),
        )

    new_values = {
        "id": mapping_id,
        "evidence_id": evidence_id,
        "control_id": control_id,
        "weightage": weightage,
        "artifact_type": artifact_type,
        "mapping_status": "pending",
    }
    create_audit_log(
        action="MAP_EVIDENCE",
        entity_type="evidence_control_mapping",
        entity_id=mapping_id,
        user_id=user_id,
        new_values=new_values,
        ip_address=ip_address,
    )

    return {
        "id": mapping_id,
        "evidence_id": evidence_id,
        "control_id": control_id,
        "weightage": weightage,
        "artifact_type": artifact_type,
        "mapping_status": "pending",
        "mapped_at": now.isoformat(),
    }


def get_mapping(mapping_id: str) -> Optional[dict[str, Any]]:
    """Get a single mapping by ID.

    Args:
        mapping_id: UUID of the mapping.

    Returns:
        Optional[dict]: Mapping record or None.
    """
    with get_cursor() as cur:
        cur.execute(_MAPPING_SELECT_BY_ID_SQL, (mapping_id,))
        row = cur.fetchone()
    return _row_to_dict(row) if row else None


def update_mapping_status(
    mapping_id: str,
    status: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """Update a mapping's status (e.g., pending -> approved/rejected).

    Args:
        mapping_id: UUID of the mapping.
        status: New status ('approved' or 'rejected').
        user_id: Optional user ID for audit.
        ip_address: Optional IP for audit.

    Returns:
        Optional[dict]: Updated mapping record, or None if not found.
    """
    with get_cursor() as cur:
        cur.execute(_MAPPING_UPDATE_STATUS_SQL, (status, mapping_id))
        row = cur.fetchone()

    if not row:
        return None

    updated = _row_to_dict(row)
    create_audit_log(
        action=f"{status.upper()}_MAPPING",
        entity_type="evidence_control_mapping",
        entity_id=mapping_id,
        user_id=user_id,
        new_values=updated,
        ip_address=ip_address,
    )
    return updated


def list_mappings_by_evidence(evidence_id: str) -> list[dict[str, Any]]:
    """List all mappings for a given evidence artifact.

    Args:
        evidence_id: UUID of the evidence.

    Returns:
        list[dict]: List of mapping records.
    """
    with get_cursor() as cur:
        cur.execute(_MAPPING_SELECT_BY_EVIDENCE_SQL, (evidence_id,))
        rows = cur.fetchall()
    return [_row_to_dict(r) for r in rows]


def list_mappings_by_control(control_id: str) -> list[dict[str, Any]]:
    """List all mappings for a given control.

    Args:
        control_id: UUID of the control.

    Returns:
        list[dict]: List of mapping records.
    """
    with get_cursor() as cur:
        cur.execute(_MAPPING_SELECT_BY_CONTROL_SQL, (control_id,))
        rows = cur.fetchall()
    return [_row_to_dict(r) for r in rows]


# =============================================================================
# Review Workflow CRUD
# =============================================================================

_REVIEW_INSERT_SQL = """
    INSERT INTO review_workflows
        (id, entity_type, entity_id, workflow_status, submitted_by,
         review_notes, created_at, updated_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""

_REVIEW_SELECT_ALL_SQL = """
    SELECT rw.id, rw.entity_type, rw.entity_id, rw.workflow_status,
           rw.submitted_by, rw.reviewed_by, rw.review_notes,
           rw.created_at, rw.updated_at,
           u_sub.username AS submitted_by_username,
           u_rev.username AS reviewed_by_username
    FROM review_workflows rw
    LEFT JOIN users u_sub ON u_sub.id = rw.submitted_by
    LEFT JOIN users u_rev ON u_rev.id = rw.reviewed_by
    ORDER BY rw.created_at DESC
"""

_REVIEW_SELECT_BY_ID_SQL = """
    SELECT rw.id, rw.entity_type, rw.entity_id, rw.workflow_status,
           rw.submitted_by, rw.reviewed_by, rw.review_notes,
           rw.created_at, rw.updated_at,
           u_sub.username AS submitted_by_username,
           u_rev.username AS reviewed_by_username
    FROM review_workflows rw
    LEFT JOIN users u_sub ON u_sub.id = rw.submitted_by
    LEFT JOIN users u_rev ON u_rev.id = rw.reviewed_by
    WHERE rw.id = %s
"""

_REVIEW_UPDATE_APPROVE_SQL = """
    UPDATE review_workflows
    SET workflow_status = 'approved',
        reviewed_by = %s,
        review_notes = COALESCE(%s, review_notes),
        updated_at = %s
    WHERE id = %s AND workflow_status = 'pending'
    RETURNING id, entity_type, entity_id, workflow_status,
              submitted_by, reviewed_by, review_notes, created_at, updated_at
"""

_REVIEW_UPDATE_REJECT_SQL = """
    UPDATE review_workflows
    SET workflow_status = 'rejected',
        reviewed_by = %s,
        review_notes = %s,
        updated_at = %s
    WHERE id = %s AND workflow_status = 'pending'
    RETURNING id, entity_type, entity_id, workflow_status,
              submitted_by, reviewed_by, review_notes, created_at, updated_at
"""


def create_review(
    entity_type: str,
    entity_id: str,
    submitted_by: Optional[str] = None,
    review_notes: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> dict[str, Any]:
    """Create a new review workflow entry.

    Args:
        entity_type: Type of entity being reviewed.
        entity_id: UUID of the entity.
        submitted_by: Optional user ID submitting the review.
        review_notes: Optional initial notes.
        ip_address: Optional IP for audit.

    Returns:
        dict: Created review record.
    """
    review_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    with get_cursor() as cur:
        cur.execute(
            _REVIEW_INSERT_SQL,
            (review_id, entity_type, entity_id, "pending", submitted_by,
             review_notes, now, now),
        )

    new_values = {
        "id": review_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "workflow_status": "pending",
        "submitted_by": submitted_by,
    }
    create_audit_log(
        action="SUBMIT_FOR_REVIEW",
        entity_type="review_workflow",
        entity_id=review_id,
        user_id=submitted_by,
        new_values=new_values,
        ip_address=ip_address,
    )

    return {
        "id": review_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "workflow_status": "pending",
        "submitted_by": submitted_by,
        "review_notes": review_notes,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }


def list_reviews() -> list[dict[str, Any]]:
    """List all review workflows.

    Returns:
        list[dict]: List of review records.
    """
    with get_cursor() as cur:
        cur.execute(_REVIEW_SELECT_ALL_SQL)
        rows = cur.fetchall()
    return [_row_to_dict(r) for r in rows]


def get_review(review_id: str) -> Optional[dict[str, Any]]:
    """Get a single review workflow by ID.

    Args:
        review_id: UUID of the review.

    Returns:
        Optional[dict]: Review record or None.
    """
    with get_cursor() as cur:
        cur.execute(_REVIEW_SELECT_BY_ID_SQL, (review_id,))
        row = cur.fetchone()
    return _row_to_dict(row) if row else None


def approve_review(
    review_id: str,
    reviewed_by: Optional[str] = None,
    review_notes: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """Approve a pending review workflow.

    Args:
        review_id: UUID of the review.
        reviewed_by: Optional user ID of the reviewer.
        review_notes: Optional approval notes.
        ip_address: Optional IP for audit.

    Returns:
        Optional[dict]: Updated review record or None if not found/already processed.
    """
    now = datetime.now(timezone.utc)

    with get_cursor() as cur:
        cur.execute(
            _REVIEW_UPDATE_APPROVE_SQL,
            (reviewed_by, review_notes, now, review_id),
        )
        row = cur.fetchone()

    if not row:
        return None

    updated = _row_to_dict(row)

    # Also update the underlying entity's status
    _update_entity_status(
        entity_type=updated["entity_type"],
        entity_id=updated["entity_id"],
        status="approved",
    )

    create_audit_log(
        action="APPROVE_REVIEW",
        entity_type="review_workflow",
        entity_id=review_id,
        user_id=reviewed_by,
        new_values=updated,
        ip_address=ip_address,
    )

    return updated


def reject_review(
    review_id: str,
    reviewed_by: Optional[str] = None,
    review_notes: str = "",
    ip_address: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """Reject a pending review workflow.

    Args:
        review_id: UUID of the review.
        reviewed_by: Optional user ID of the reviewer.
        review_notes: Required rejection notes.
        ip_address: Optional IP for audit.

    Returns:
        Optional[dict]: Updated review record or None if not found/already processed.
    """
    now = datetime.now(timezone.utc)

    with get_cursor() as cur:
        cur.execute(
            _REVIEW_UPDATE_REJECT_SQL,
            (reviewed_by, review_notes, now, review_id),
        )
        row = cur.fetchone()

    if not row:
        return None

    updated = _row_to_dict(row)

    # Also update the underlying entity's status
    _update_entity_status(
        entity_type=updated["entity_type"],
        entity_id=updated["entity_id"],
        status="rejected",
    )

    create_audit_log(
        action="REJECT_REVIEW",
        entity_type="review_workflow",
        entity_id=review_id,
        user_id=reviewed_by,
        new_values=updated,
        ip_address=ip_address,
    )

    return updated


def _update_entity_status(
    entity_type: str,
    entity_id: str,
    status: str,
) -> None:
    """Update the status of the entity associated with a review.

    Supports updating evidence_control_mapping status.

    Args:
        entity_type: Type of entity to update.
        entity_id: UUID of the entity.
        status: New status value.
    """
    if entity_type == "evidence_control_mapping":
        with get_cursor() as cur:
            cur.execute(
                "UPDATE evidence_control_mappings SET mapping_status = %s WHERE id = %s",
                (status, entity_id),
            )


# =============================================================================
# Audit Log Queries
# =============================================================================

_AUDIT_SELECT_ALL_SQL = """
    SELECT al.id, al.user_id, al.action, al.entity_type, al.entity_id,
           al.old_values, al.new_values, al.ip_address, al.created_at,
           u.username AS user_username
    FROM audit_logs al
    LEFT JOIN users u ON u.id = al.user_id
    ORDER BY al.created_at DESC
"""


def list_audit_logs(
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    actions: Optional[list[str]] = None,
    user_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    entity_id_search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """List audit log entries with optional filtering.

    Args:
        action: Optional single action filter (legacy).
        entity_type: Optional entity type filter.
        actions: Optional list of action types to filter by (multi-select).
        user_id: Optional user ID filter.
        date_from: Optional ISO date string to filter from (inclusive).
        date_to: Optional ISO date string to filter to (inclusive).
        entity_id_search: Optional search string for entity_id (partial match).
        limit: Maximum number of records (default 100).
        offset: Pagination offset.

    Returns:
        list[dict]: List of audit log records.
    """
    query = _AUDIT_SELECT_ALL_SQL
    params: list[Any] = []
    conditions: list[str] = []

    if action:
        conditions.append("al.action = %s")
        params.append(action)

    if actions:
        placeholders = ", ".join(["%s"] * len(actions))
        conditions.append(f"al.action IN ({placeholders})")
        params.extend(actions)

    if entity_type:
        conditions.append("al.entity_type = %s")
        params.append(entity_type)

    if user_id:
        conditions.append("al.user_id = %s")
        params.append(user_id)

    if date_from:
        conditions.append("al.created_at >= %s::timestamp")
        params.append(date_from)

    if date_to:
        conditions.append("al.created_at <= %s::timestamp")
        params.append(date_to)

    if entity_id_search:
        conditions.append("al.entity_id::text LIKE %s")
        params.append(f"%{entity_id_search}%")

    if conditions:
        # Remove ORDER BY from base query, add WHERE conditions, then re-add ORDER BY
        query = query.replace("ORDER BY al.created_at DESC", "")
        query += " WHERE " + " AND ".join(conditions) + " "
        query += "ORDER BY al.created_at DESC"

    query += " LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    with get_cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()
    return [_row_to_dict(r) for r in rows]


# =============================================================================
# Compliance Score Calculation
# =============================================================================

_CONTROL_APPROVED_MAPPINGS_SQL = """
    SELECT ecm.control_id, ecm.weightage
    FROM evidence_control_mappings ecm
    WHERE ecm.control_id = %s AND ecm.mapping_status = 'approved'
"""

_CONTROL_ARTIFACT_REQUIREMENTS_SQL = """
    SELECT artifact_requirements
    FROM controls
    WHERE id = %s
"""


def calculate_compliance_score() -> dict[str, Any]:
    """Calculate the overall compliance score across all controls.

    Formula:
        Each control's score = (sum of validated evidence weightage / total required weightage) * 100
        Overall score = weighted average across all controls

    Returns:
        dict: Compliance scores with per-control breakdown.
    """
    with get_cursor() as cur:
        # Get all controls
        cur.execute("SELECT id, control_id, title, artifact_requirements FROM controls")
        all_controls = cur.fetchall()

    control_scores: list[dict[str, Any]] = []
    total_weighted_score = 0.0
    total_max_weightage = 0.0

    for ctrl in all_controls:
        ctrl_id = ctrl["id"]
        ctrl_ref_id = ctrl["control_id"]
        title = ctrl["title"]
        requirements = ctrl["artifact_requirements"] or []

        # Calculate total required weightage from artifact requirements
        total_required = sum(
            float(req.get("weightage", 0)) for req in requirements
        )

        # Get sum of weightages from approved mappings
        with get_cursor() as cur2:
            cur2.execute(_CONTROL_APPROVED_MAPPINGS_SQL, (ctrl_id,))
            approved_mappings = cur2.fetchall()

        validated_weightage = sum(
            float(m["weightage"]) for m in approved_mappings
        )

        # Count distinct evidence artifacts mapped (any status) to this control
        with get_cursor() as cur3:
            cur3.execute(
                "SELECT COUNT(DISTINCT evidence_id) as cnt FROM evidence_control_mappings WHERE control_id = %s",
                (ctrl_id,),
            )
            evidence_count = cur3.fetchone()["cnt"] or 0

        # Calculate control score
        if total_required > 0:
            control_score = min(
                (validated_weightage / total_required) * 100, 100.0
            )
        else:
            control_score = 0.0

        control_scores.append({
            "control_id": ctrl_ref_id,
            "title": title,
            "total_required_weightage": total_required,
            "validated_weightage": validated_weightage,
            "score": round(control_score, 2),
            "status": _score_to_status(control_score),
            "evidence_count": evidence_count,
        })

        total_weighted_score += control_score
        total_max_weightage += 100.0

    # Overall score is the average of all control scores
    overall_score = (
        round(total_weighted_score / len(control_scores), 2)
        if control_scores
        else 0.0
    )

    return {
        "overall_score": overall_score,
        "overall_status": _score_to_status(overall_score),
        "total_controls": len(control_scores),
        "controls": control_scores,
    }


def get_gap_summary() -> dict[str, Any]:
    """Compute gap summary for all controls.

    A gap is a required artifact type that does not have an approved
    evidence mapping. Severity is based on weightage: critical > 25%,
    high > 15%, medium > 5%, low <= 5%.

    Returns:
        dict: Gap summary with total_open_gaps, gaps_by_severity,
              and oldest_open_gap_age_days.
    """
    with get_cursor() as cur:
        cur.execute("SELECT id, control_id, title, artifact_requirements FROM controls")
        all_controls = cur.fetchall()

    total_gaps = 0
    gaps_by_severity: dict[str, int] = {
        "critical": 0, "high": 0, "medium": 0, "low": 0
    }
    oldest_gap_age = 0

    for ctrl in all_controls:
        ctrl_id = ctrl["id"]
        requirements = ctrl["artifact_requirements"] or []

        # Get approved artifact types for this control
        with get_cursor() as cur2:
            cur2.execute(
                "SELECT DISTINCT artifact_type FROM evidence_control_mappings "
                "WHERE control_id = %s AND mapping_status = 'approved'",
                (ctrl_id,),
            )
            approved_types = {r["artifact_type"] for r in cur2.fetchall() if r["artifact_type"]}

        for req in requirements:
            req_type = req.get("type", "")
            weightage = float(req.get("weightage", 0))

            if req_type not in approved_types:
                total_gaps += 1
                if weightage >= 25.0:
                    gaps_by_severity["critical"] += 1
                elif weightage >= 15.0:
                    gaps_by_severity["high"] += 1
                elif weightage >= 5.0:
                    gaps_by_severity["medium"] += 1
                else:
                    gaps_by_severity["low"] += 1

    return {
        "total_open_gaps": total_gaps,
        "gaps_by_severity": gaps_by_severity,
        "oldest_open_gap_age_days": oldest_gap_age,
    }


def get_risk_heatmap() -> list[dict[str, Any]]:
    """Compute risk heatmap data for all controls.

    Returns a list of data points for each control × risk level combination.
    Color is based on mapping status: green (Fully Mapped), yellow (Partially Mapped),
    red (Unmapped).

    Returns:
        list[dict]: Heatmap data points with control_id, risk_level, status, color.
    """
    risk_levels = ["low", "medium", "high", "critical"]

    with get_cursor() as cur:
        cur.execute("SELECT id, control_id, title, artifact_requirements FROM controls")
        all_controls = cur.fetchall()

    heatmap_data = []

    for ctrl in all_controls:
        ctrl_id_uuid = ctrl["id"]
        ctrl_ref_id = ctrl["control_id"]
        requirements = ctrl["artifact_requirements"] or []

        # Calculate compliance score for this control
        total_required = sum(
            float(req.get("weightage", 0)) for req in requirements
        )

        with get_cursor() as cur2:
            cur2.execute(_CONTROL_APPROVED_MAPPINGS_SQL, (ctrl_id_uuid,))
            approved_mappings = cur2.fetchall()

        validated_weightage = sum(
            float(m["weightage"]) for m in approved_mappings
        )

        if total_required > 0:
            control_score = min(
                (validated_weightage / total_required) * 100, 100.0
            )
        else:
            control_score = 0.0

        status = _score_to_status(control_score)
        color = _get_heatmap_color(status)

        heatmap_data.append({
            "control_id": ctrl_ref_id,
            "status": status,
            "score": round(control_score, 2),
            "color": color,
        })

    return heatmap_data


def _get_heatmap_color(status: str) -> str:
    """Get the heatmap color for a mapping status.

    Args:
        status: Mapping status string.

    Returns:
        str: CSS color hex code.
    """
    colors = {
        "Fully Mapped": "#00cc66",
        "Partially Mapped": "#ffcc00",
        "Unmapped": "#ff3333",
    }
    return colors.get(status, "#999999")


def _score_to_status(score: float) -> str:
    """Convert a numeric score to a status string.

    Args:
        score: Percentage score (0-100).

    Returns:
        str: Status: 'Fully Mapped', 'Partially Mapped', or 'Unmapped'.
    """
    if score >= 90.0:
        return "Fully Mapped"
    elif score >= 50.0:
        return "Partially Mapped"
    else:
        return "Unmapped"


# =============================================================================
# User helpers
# =============================================================================

_USER_SELECT_BY_ID_SQL = """
    SELECT id, username, email, full_name, role, is_active, created_at
    FROM users WHERE id = %s
"""

_USER_SELECT_BY_USERNAME_SQL = """
    SELECT id, username, email, full_name, role, is_active, created_at
    FROM users WHERE username = %s
"""


def get_user(user_id: str) -> Optional[dict[str, Any]]:
    """Get a user by ID.

    Args:
        user_id: UUID of the user.

    Returns:
        Optional[dict]: User record or None.
    """
    with get_cursor() as cur:
        cur.execute(_USER_SELECT_BY_ID_SQL, (user_id,))
        row = cur.fetchone()
    return _row_to_dict(row) if row else None


def list_users() -> list[dict[str, Any]]:
    """List all registered users.

    Returns:
        list[dict]: List of user records.
    """
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, username, email, full_name, role, is_active, created_at "
            "FROM users ORDER BY username"
        )
        rows = cur.fetchall()
    return [_row_to_dict(r) for r in rows]


def get_user_by_username(username: str) -> Optional[dict[str, Any]]:
    """Get a user by username.

    Args:
        username: Username to look up.

    Returns:
        Optional[dict]: User record or None.
    """
    with get_cursor() as cur:
        cur.execute(_USER_SELECT_BY_USERNAME_SQL, (username,))
        row = cur.fetchone()
    return _row_to_dict(row) if row else None


# =============================================================================
# Knowledge Base CRUD
# =============================================================================

_KNOWLEDGE_INSERT_SQL = """
    INSERT INTO knowledge_base
        (id, title, content, source, chunk_index, embedding_vector, metadata, created_at)
    VALUES (%s, %s, %s, %s, %s, %s::vector, %s::jsonb, %s)
"""

_KNOWLEDGE_SELECT_BY_ID_SQL = """
    SELECT id, title, content, source, chunk_index, metadata, created_at
    FROM knowledge_base
    WHERE id = %s
"""

_KNOWLEDGE_DELETE_BY_SOURCE_SQL = """
    DELETE FROM knowledge_base WHERE source = %s
"""

_KNOWLEDGE_COUNT_SQL = """
    SELECT COUNT(*) as cnt FROM knowledge_base
"""


def create_knowledge_entry(
    title: str,
    content: str,
    source: str = "user_upload",
    chunk_index: int = 0,
    embedding_vector: Optional[list[float]] = None,
    metadata: Optional[dict[str, Any]] = None,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> dict[str, Any]:
    """Create a new entry in the knowledge_base table.

    Stores a document chunk with its embedding vector and metadata
    for vector similarity search.

    Args:
        title: Title of the knowledge entry.
        content: Text content of the entry.
        source: Source identifier (default: "user_upload").
        chunk_index: Index of this chunk within the document.
        embedding_vector: Optional 1024-dim embedding vector.
        metadata: Optional metadata dict (control_id, framework, category, etc.).
        user_id: Optional user ID for audit logging.
        ip_address: Optional IP for audit logging.

    Returns:
        dict: Created knowledge entry record.
    """
    entry_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    vector_str = None
    if embedding_vector:
        vector_str = "[" + ",".join(str(v) for v in embedding_vector) + "]"

    with get_cursor() as cur:
        cur.execute(
            _KNOWLEDGE_INSERT_SQL,
            (
                entry_id,
                title,
                content,
                source,
                chunk_index,
                vector_str,
                json_dumps(metadata or {}),
                now,
            ),
        )

    new_values = {
        "id": entry_id,
        "title": title,
        "source": source,
        "chunk_index": chunk_index,
    }
    create_audit_log(
        action="CREATE_KNOWLEDGE",
        entity_type="knowledge_base",
        entity_id=entry_id,
        user_id=user_id,
        new_values=new_values,
        ip_address=ip_address,
    )

    return {
        "id": entry_id,
        "title": title,
        "content": content,
        "source": source,
        "chunk_index": chunk_index,
        "metadata": metadata or {},
        "created_at": now.isoformat(),
    }


def get_knowledge_entry(entry_id: str) -> Optional[dict[str, Any]]:
    """Get a single knowledge base entry by ID.

    Args:
        entry_id: UUID of the knowledge entry.

    Returns:
        Optional[dict]: Knowledge entry record or None.
    """
    with get_cursor() as cur:
        cur.execute(_KNOWLEDGE_SELECT_BY_ID_SQL, (entry_id,))
        row = cur.fetchone()
    return _row_to_dict(row) if row else None


def delete_knowledge_by_source(source: str) -> int:
    """Delete all knowledge entries with a given source.

    Args:
        source: Source identifier to delete entries for.

    Returns:
        int: Number of deleted entries.
    """
    with get_cursor() as cur:
        cur.execute(_KNOWLEDGE_DELETE_BY_SOURCE_SQL, (source,))
        deleted = cur.rowcount
    return deleted


def count_knowledge_entries() -> int:
    """Count total knowledge base entries.

    Returns:
        int: Total count of entries.
    """
    with get_cursor() as cur:
        cur.execute(_KNOWLEDGE_COUNT_SQL)
        row = cur.fetchone()
    return row["cnt"] if row else 0


# =============================================================================
# Agent Sessions CRUD
# =============================================================================

_SESSION_INSERT_SQL = """
    INSERT INTO agent_sessions
        (id, user_id, session_type, context, memory_summary, started_at)
    VALUES (%s, %s, %s, %s::jsonb, %s, %s)
"""

_SESSION_SELECT_ALL_SQL = """
    SELECT id, user_id, session_type, context, memory_summary, started_at
    FROM agent_sessions
    ORDER BY started_at DESC
"""

_SESSION_SELECT_BY_ID_SQL = """
    SELECT id, user_id, session_type, context, memory_summary, started_at
    FROM agent_sessions
    WHERE id = %s
"""

_SESSION_UPDATE_SQL = """
    UPDATE agent_sessions
    SET context = %s::jsonb,
        memory_summary = %s
    WHERE id = %s
"""

_SESSION_DELETE_SQL = """
    DELETE FROM agent_sessions WHERE id = %s
"""


def create_agent_session(
    session_id: str,
    user_id: Optional[str] = None,
    session_type: str = "grc_chatbot",
    context: Optional[dict[str, Any]] = None,
    memory_summary: Optional[str] = None,
) -> dict[str, Any]:
    """Create a new agent session record.

    Args:
        session_id: UUID for the session.
        user_id: Optional user identifier.
        session_type: Type of agent session (default: "grc_chatbot").
        context: Optional JSON-serializable context dict.
        memory_summary: Optional text summary of the conversation.

    Returns:
        dict: Created session record.
    """
    now = datetime.now(timezone.utc)

    with get_cursor() as cur:
        cur.execute(
            _SESSION_INSERT_SQL,
            (
                session_id,
                user_id,
                session_type,
                json_dumps(context or {}),
                memory_summary or "",
                now,
            ),
        )

    return {
        "id": session_id,
        "user_id": user_id,
        "session_type": session_type,
        "context": context or {},
        "memory_summary": memory_summary or "",
        "started_at": now.isoformat(),
    }


def list_agent_sessions(
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """List all agent sessions, most recent first.

    Args:
        limit: Maximum records to return (default 50).
        offset: Pagination offset (default 0).

    Returns:
        list[dict]: List of session records.
    """
    with get_cursor() as cur:
        query = _SESSION_SELECT_ALL_SQL + " LIMIT %s OFFSET %s"
        cur.execute(query, (limit, offset))
        rows = cur.fetchall()
    return [_row_to_dict(r) for r in rows]


def get_agent_session(session_id: str) -> Optional[dict[str, Any]]:
    """Get a single agent session by ID.

    Args:
        session_id: UUID of the session.

    Returns:
        Optional[dict]: Session record or None if not found.
    """
    with get_cursor() as cur:
        cur.execute(_SESSION_SELECT_BY_ID_SQL, (session_id,))
        row = cur.fetchone()
    return _row_to_dict(row) if row else None


def update_agent_session(
    session_id: str,
    context: Optional[dict[str, Any]] = None,
    memory_summary: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """Update an agent session's context and memory summary.

    Args:
        session_id: UUID of the session to update.
        context: New context dict to store.
        memory_summary: New memory summary text.

    Returns:
        Optional[dict]: Updated session record, or None if not found.
    """
    existing = get_agent_session(session_id)
    if not existing:
        return None

    new_context = context if context is not None else existing.get("context", {})
    new_summary = memory_summary if memory_summary is not None else existing.get("memory_summary", "")

    with get_cursor() as cur:
        cur.execute(
            _SESSION_UPDATE_SQL,
            (json_dumps(new_context), new_summary, session_id),
        )

    return get_agent_session(session_id)


def delete_agent_session(session_id: str) -> bool:
    """Delete an agent session.

    Args:
        session_id: UUID of the session to delete.

    Returns:
        bool: True if deleted, False if not found.
    """
    with get_cursor() as cur:
        cur.execute(_SESSION_DELETE_SQL, (session_id,))
        return cur.rowcount > 0


def count_agent_sessions() -> int:
    """Count total agent sessions.

    Returns:
        int: Total count of sessions.
    """
    with get_cursor() as cur:
        cur.execute("SELECT COUNT(*) as cnt FROM agent_sessions")
        row = cur.fetchone()
    return row["cnt"] if row else 0


# =============================================================================
# Utility Functions
# =============================================================================

_SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".docx"}


def get_supported_extensions() -> set[str]:
    """Get the set of supported file extensions for evidence upload.

    Returns:
        set[str]: Set of supported file extensions.
    """
    return _SUPPORTED_EXTENSIONS


def is_supported_file_type(filename: str) -> bool:
    """Check if a file type is supported for evidence upload.

    Args:
        filename: Name of the file to check.

    Returns:
        bool: True if the file type is supported.
    """
    ext = os.path.splitext(filename)[1].lower()
    return ext in _SUPPORTED_EXTENSIONS


def compute_checksum(file_path: str) -> str:
    """Compute SHA-256 checksum of a file.

    Args:
        file_path: Absolute path to the file.

    Returns:
        str: Hex digest of the SHA-256 hash.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def json_dumps(obj: Any) -> str:
    """Serialize an object to JSON string for PostgreSQL JSONB.

    Args:
        obj: Object to serialize.

    Returns:
        str: JSON string.
    """
    import json
    return json.dumps(obj, default=str)


def _row_to_dict(row: RealDictRow) -> dict[str, Any]:
    """Convert a RealDictRow to a plain dictionary with ISO-formatted datetimes.

    Args:
        row: Database row from RealDictCursor.

    Returns:
        dict: Plain dictionary with formatted values.
    """
    result: dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, datetime):
            result[key] = value.isoformat()
        elif isinstance(value, bytes):
            result[key] = value.hex()
        else:
            result[key] = value
    return result
