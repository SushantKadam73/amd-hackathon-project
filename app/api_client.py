"""GRC Platform - API Client for FastAPI Backend.

Provides helper functions for all Streamlit pages to call the backend API.
Handles connection errors, loading states, and response parsing.
"""

from typing import Any, Optional

import requests
import streamlit as st

# Base URL for the FastAPI backend
API_BASE_URL = "http://localhost:8000"


def _get(endpoint: str) -> Optional[dict[str, Any]]:
    """Make a GET request to the API.

    Args:
        endpoint: API endpoint path (e.g., '/api/v1/frameworks').

    Returns:
        Parsed JSON response as dict, or None if request fails.
    """
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot connect to API at {API_BASE_URL}. Is the backend running?")
        return None
    except requests.exceptions.Timeout:
        st.error("API request timed out. Please try again.")
        return None
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code
        if status == 404:
            return None
        detail = e.response.json().get("detail", str(e))
        st.error(f"API error ({status}): {detail}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return None


def _get_list(endpoint: str) -> list[dict[str, Any]]:
    """Make a GET request expecting a list response.

    Args:
        endpoint: API endpoint path.

    Returns:
        List of items from the API response, or empty list on failure.
    """
    result = _get(endpoint)
    if result is None:
        return []
    return result.get("items", [])


# =============================================================================
# Framework Operations
# =============================================================================


def get_frameworks() -> list[dict[str, Any]]:
    """Fetch all compliance frameworks.

    Returns:
        List of framework dicts with id, name, version, description, created_at.
    """
    return _get_list("/api/v1/frameworks")


def get_framework(framework_id: str) -> Optional[dict[str, Any]]:
    """Fetch a single framework by UUID.

    Args:
        framework_id: UUID of the framework.

    Returns:
        Framework dict, or None if not found.
    """
    return _get(f"/api/v1/frameworks/{framework_id}")


# =============================================================================
# Control Operations
# =============================================================================


def get_controls(framework_id: str) -> list[dict[str, Any]]:
    """Fetch all controls for a given framework.

    Args:
        framework_id: UUID of the framework.

    Returns:
        List of control dicts with full details including
        artifact_requirements and cross_framework_mappings.
    """
    return _get_list(f"/api/v1/frameworks/{framework_id}/controls")


def get_compliance_status() -> Optional[dict[str, Any]]:
    """Fetch the overall compliance score and per-control breakdown.

    Returns:
        Dict with overall_score, overall_status, total_controls, controls[].
        Each control has control_id, title, total_required_weightage,
        validated_weightage, score, status.
    """
    return _get("/api/v1/reports/compliance-status")


# =============================================================================
# Evidence Operations
# =============================================================================


def get_evidence_list() -> list[dict[str, Any]]:
    """Fetch all uploaded evidence artifacts.

    Returns:
        List of evidence dicts with id, name, file_type, file_size,
        checksum, content_text, uploaded_at.
    """
    return _get_list("/api/v1/evidence")


def get_evidence_detail(evidence_id: str) -> Optional[dict[str, Any]]:
    """Fetch a single evidence artifact by UUID.

    Args:
        evidence_id: UUID of the evidence artifact.

    Returns:
        Evidence dict with full metadata, or None if not found.
    """
    return _get(f"/api/v1/evidence/{evidence_id}")


def get_evidence_mappings(evidence_id: str) -> list[dict[str, Any]]:
    """Fetch all control mappings for an evidence artifact.

    Args:
        evidence_id: UUID of the evidence artifact.

    Returns:
        List of mapping dicts with control_ref_id, control_title,
        weightage, artifact_type, mapping_status.
    """
    return _get_list(f"/api/v1/evidence/{evidence_id}/mappings")


def upload_evidence(
    file_content: bytes,
    filename: str,
    uploaded_by: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """Upload an evidence artifact file to the API.

    Args:
        file_content: Raw file content as bytes.
        filename: Name of the file (must have supported extension).
        uploaded_by: Optional user UUID string.

    Returns:
        Evidence response dict on success, None on failure.
    """
    try:
        files = {"file": (filename, file_content)}
        params = {}
        if uploaded_by:
            params["uploaded_by"] = uploaded_by

        response = requests.post(
            f"{API_BASE_URL}/api/v1/evidence",
            files=files,
            params=params,
            timeout=60,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code
        detail = e.response.json().get("detail", str(e))
        st.error(f"Upload failed ({status}): {detail}")
        return None
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot connect to API at {API_BASE_URL}. Is the backend running?")
        return None
    except requests.exceptions.Timeout:
        st.error("Upload request timed out. Please try again.")
        return None
    except Exception as e:
        st.error(f"Unexpected upload error: {e}")
        return None


# =============================================================================
# Dashboard & Reports
# =============================================================================


def get_gap_summary() -> Optional[dict[str, Any]]:
    """Fetch the gap summary report.

    Returns:
        Dict with total_open_gaps, gaps_by_severity, oldest_open_gap_age_days,
        or None on failure.
    """
    return _get("/api/v1/reports/gap-summary")


def get_risk_heatmap() -> list[dict[str, Any]]:
    """Fetch the risk heatmap data.

    Returns:
        List of dicts with control_id, status, score, color for each control,
        or empty list on failure.
    """
    result = _get("/api/v1/reports/risk-heatmap")
    if result is None:
        return []
    return result.get("items", [])


# =============================================================================
# Review Workflow Operations
# =============================================================================


def get_reviews() -> list[dict[str, Any]]:
    """Fetch all review workflow entries.

    Returns:
        List of review dicts with id, entity_type, entity_id,
        workflow_status, submitted_by, reviewed_by, review_notes,
        created_at, updated_at, submitted_by_username, reviewed_by_username.
    """
    return _get_list("/api/v1/reviews")


def get_review(review_id: str) -> Optional[dict[str, Any]]:
    """Fetch a single review workflow by ID.

    Args:
        review_id: UUID of the review.

    Returns:
        Review dict, or None if not found.
    """
    return _get(f"/api/v1/reviews/{review_id}")


def submit_for_review(
    entity_type: str,
    entity_id: str,
    review_notes: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """Submit an entity for review.

    Creates a review workflow record with status 'pending'.

    Args:
        entity_type: Type of entity being reviewed (e.g., 'evidence_control_mapping').
        entity_id: UUID of the entity.
        review_notes: Optional submission notes.

    Returns:
        Review response dict on success, None on failure.
    """
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/reviews",
            json={
                "entity_type": entity_type,
                "entity_id": entity_id,
                "review_notes": review_notes,
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code
        detail = e.response.json().get("detail", str(e))
        st.error(f"Submit for review failed ({status}): {detail}")
        return None
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot connect to API at {API_BASE_URL}. Is the backend running?")
        return None
    except requests.exceptions.Timeout:
        st.error("Request timed out. Please try again.")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return None


def approve_review(
    review_id: str,
    reviewer_id: str,
    review_notes: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """Approve a pending review.

    Args:
        review_id: UUID of the review.
        reviewer_id: UUID of the reviewer.
        review_notes: Optional approval notes.

    Returns:
        Updated review dict on success, None on failure.
    """
    try:
        response = requests.put(
            f"{API_BASE_URL}/api/v1/reviews/{review_id}/approve",
            json={
                "reviewer_id": reviewer_id,
                "review_notes": review_notes,
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code
        detail = e.response.json().get("detail", str(e))
        if status == 403:
            st.error(f"Self-approval not allowed: {detail}")
        elif status == 409:
            st.warning(f"Review already processed: {detail}")
        else:
            st.error(f"Approve failed ({status}): {detail}")
        return None
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot connect to API at {API_BASE_URL}. Is the backend running?")
        return None
    except requests.exceptions.Timeout:
        st.error("Request timed out. Please try again.")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return None


def reject_review(
    review_id: str,
    reviewer_id: str,
    review_notes: str,
) -> Optional[dict[str, Any]]:
    """Reject a pending review with mandatory notes.

    Args:
        review_id: UUID of the review.
        reviewer_id: UUID of the reviewer.
        review_notes: Required rejection notes (must be non-empty).

    Returns:
        Updated review dict on success, None on failure.
    """
    try:
        response = requests.put(
            f"{API_BASE_URL}/api/v1/reviews/{review_id}/reject",
            json={
                "reviewer_id": reviewer_id,
                "review_notes": review_notes,
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code
        detail = e.response.json().get("detail", str(e))
        if status == 422:
            st.error(f"Validation error: {detail}")
        elif status == 409:
            st.warning(f"Review already processed: {detail}")
        else:
            st.error(f"Reject failed ({status}): {detail}")
        return None
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot connect to API at {API_BASE_URL}. Is the backend running?")
        return None
    except requests.exceptions.Timeout:
        st.error("Request timed out. Please try again.")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return None


def get_pending_review_count() -> int:
    """Get the count of pending reviews.

    Returns:
        Number of reviews with workflow_status 'pending'.
    """
    reviews = get_reviews()
    if reviews is None:
        return 0
    return sum(1 for r in reviews if r.get("workflow_status") == "pending")


# =============================================================================
# User Operations
# =============================================================================


def get_users() -> list[dict[str, Any]]:
    """Fetch all registered users.

    Returns:
        List of user dicts with id, username, email, full_name, role.
    """
    result = _get("/api/v1/users")
    if result is None:
        return []
    return result.get("items", [])


# =============================================================================
# Audit Log Operations
# =============================================================================


def get_audit_logs(
    actions: Optional[list[str]] = None,
    user_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    entity_id_search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Fetch audit log entries with optional filtering.

    Args:
        actions: Optional list of action types to filter by.
        user_id: Optional user ID to filter by.
        date_from: Optional ISO date string to filter from.
        date_to: Optional ISO date string to filter to.
        entity_id_search: Optional search string for entity ID.
        limit: Maximum records to return (default 100).
        offset: Pagination offset (default 0).

    Returns:
        List of audit log entry dicts with id, user_id, action, entity_type,
        entity_id, old_values, new_values, ip_address, created_at, user_username.
    """
    params: list[str] = []
    if actions:
        params.append(f"actions={','.join(actions)}")
    if user_id:
        params.append(f"user_id={user_id}")
    if date_from:
        params.append(f"date_from={date_from}")
    if date_to:
        params.append(f"date_to={date_to}")
    if entity_id_search:
        params.append(f"entity_id_search={entity_id_search}")
    params.append(f"limit={limit}")
    params.append(f"offset={offset}")

    query_string = "&".join(params)
    result = _get(f"/api/v1/audit-logs?{query_string}")
    if result is None:
        return []
    return result.get("items", [])


def get_mapping_detail(mapping_id: str) -> Optional[dict[str, Any]]:
    """Fetch a single evidence-control mapping by ID.

    Args:
        mapping_id: UUID of the mapping.

    Returns:
        Mapping dict with evidence and control details, or None.
    """
    return _get(f"/api/v1/evidence/mappings/{mapping_id}")


def map_evidence_to_control(
    evidence_id: str,
    control_id: str,
    weightage: float,
    artifact_type: str,
) -> Optional[dict[str, Any]]:
    """Map an evidence artifact to a control.

    Args:
        evidence_id: UUID of the evidence artifact.
        control_id: UUID of the target control.
        weightage: Weightage percentage for this artifact type.
        artifact_type: Type of artifact being mapped.

    Returns:
        Mapping response dict on success, None on failure.
    """
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/evidence/{evidence_id}/map-to-control",
            json={
                "control_id": control_id,
                "weightage": weightage,
                "artifact_type": artifact_type,
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code
        detail = e.response.json().get("detail", str(e))
        st.error(f"Mapping failed ({status}): {detail}")
        return None
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot connect to API at {API_BASE_URL}. Is the backend running?")
        return None
    except requests.exceptions.Timeout:
        st.error("Mapping request timed out. Please try again.")
        return None
    except Exception as e:
        st.error(f"Unexpected mapping error: {e}")
        return None


# =============================================================================
# Chat & Agent Session Operations
# =============================================================================


def analyze_evidence_ai(evidence_id: str) -> Optional[dict[str, Any]]:
    """Analyze an evidence artifact using AI.

    Args:
        evidence_id: UUID of the evidence artifact.

    Returns:
        Analysis response dict with relevance_scores, suggested_artifact_type,
        quality_assessment, currency, confidence, requires_review. None on failure.
    """
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/agent/analyze-evidence",
            json={"evidence_id": evidence_id},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code
        detail = e.response.json().get("detail", str(e))
        st.error(f"AI analysis failed ({status}): {detail}")
        return None
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot connect to API at {API_BASE_URL}. Is the backend running?")
        return None
    except requests.exceptions.Timeout:
        st.error("AI analysis timed out. Please try again.")
        return None
    except Exception as e:
        st.error(f"Unexpected AI analysis error: {e}")
        return None


def suggest_mapping_ai(evidence_id: str) -> Optional[dict[str, Any]]:
    """Get AI-suggested control mappings for an evidence artifact.

    Args:
        evidence_id: UUID of the evidence artifact.

    Returns:
        Suggestion response dict with evidence_id, evidence_name,
        suggestions list. None on failure.
    """
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/agent/suggest-mapping",
            json={"evidence_id": evidence_id},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code
        detail = e.response.json().get("detail", str(e))
        st.error(f"Mapping suggestion failed ({status}): {detail}")
        return None
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot connect to API at {API_BASE_URL}. Is the backend running?")
        return None
    except requests.exceptions.Timeout:
        st.error("Mapping suggestion timed out. Please try again.")
        return None
    except Exception as e:
        st.error(f"Unexpected mapping suggestion error: {e}")
        return None


def send_chat_message(
    message: str,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """Send a chat message to the GRC Chatbot Agent.

    Args:
        message: The user's chat message text.
        session_id: Optional session ID for continuing a conversation.
        user_id: Optional user identifier.

    Returns:
        Dict with 'response' and 'session_id' keys on success, None on failure.
    """
    try:
        payload: dict[str, Any] = {"message": message}
        if session_id:
            payload["session_id"] = session_id
        if user_id:
            payload["user_id"] = user_id

        response = requests.post(
            f"{API_BASE_URL}/api/v1/agent/chat",
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code
        detail = e.response.json().get("detail", str(e))
        if status == 503:
            st.error("The AI service is temporarily unavailable. Please try again later.")
        elif status == 400:
            st.warning(f"{detail}")
        elif status == 422:
            st.warning("Please type a question to get started.")
        else:
            st.error(f"Chat error ({status}): {detail}")
        return None
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot connect to API at {API_BASE_URL}. Is the backend running?")
        return None
    except requests.exceptions.Timeout:
        st.error("Chat request timed out. Please try again.")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return None


def get_agent_sessions(limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    """Fetch all agent chat sessions.

    Args:
        limit: Maximum records to return (default 50).
        offset: Pagination offset (default 0).

    Returns:
        List of session dicts with id, user_id, session_type,
        memory_summary, started_at.
    """
    result = _get(f"/api/v1/agent/sessions?limit={limit}&offset={offset}")
    if result is None:
        return []
    return result.get("items", [])


def get_agent_session(session_id: str) -> Optional[dict[str, Any]]:
    """Fetch a single agent session by ID.

    Args:
        session_id: UUID of the session.

    Returns:
        Session dict, or None if not found.
    """
    return _get(f"/api/v1/agent/sessions/{session_id}")


def delete_agent_session(session_id: str) -> bool:
    """Delete an agent session.

    Args:
        session_id: UUID of the session to delete.

    Returns:
        True if deleted, False otherwise.
    """
    try:
        response = requests.delete(
            f"{API_BASE_URL}/api/v1/agent/sessions/{session_id}",
            timeout=10,
        )
        response.raise_for_status()
        return True
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            st.warning("Session not found.")
        else:
            detail = e.response.json().get("detail", str(e))
            st.error(f"Delete failed ({e.response.status_code}): {detail}")
        return False
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot connect to API at {API_BASE_URL}. Is the backend running?")
        return False
    except requests.exceptions.Timeout:
        st.error("Request timed out. Please try again.")
        return False
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return False
