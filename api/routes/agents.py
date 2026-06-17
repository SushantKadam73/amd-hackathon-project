"""GRC Platform - Agent API Routes.

FastAPI routes for:
- POST /api/v1/agent/chat - Chat with the GRC Chatbot Agent
- POST /api/v1/agent/analyze-evidence - Analyze evidence artifact
- POST /api/v1/agent/suggest-mapping - Suggest evidence-to-control mapping
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from config import get_config

config = get_config()

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


# =============================================================================
# Request / Response Schemas
# =============================================================================

class ChatRequest(BaseModel):
    """Request schema for the chat endpoint."""

    message: str = Field(
        ..., min_length=1, max_length=10000,
        description="The user's chat message."
    )
    user_id: Optional[str] = Field(
        None, description="Optional user identifier."
    )
    session_id: Optional[str] = Field(
        None, description="Optional session identifier."
    )


class ChatResponse(BaseModel):
    """Response schema for the chat endpoint."""

    response: str = Field(
        ..., description="The chatbot's response message."
    )
    session_id: Optional[str] = Field(
        None, description="Session identifier for continued conversation."
    )


class ErrorResponse(BaseModel):
    """Response schema for error conditions."""

    error: str = Field(
        ..., description="A user-friendly error message."
    )


class AnalyzeEvidenceRequest(BaseModel):
    """Request schema for the evidence analysis endpoint."""

    evidence_id: str = Field(
        ..., description="UUID of the evidence artifact to analyze."
    )


class RelevanceScore(BaseModel):
    """Relevance score for a single control."""

    control_id: str = Field(
        ..., description="NIST SP 800-53 control ID."
    )
    score: float = Field(
        ..., ge=0, le=100,
        description="Relevance score from 0-100."
    )


class CurrencyAssessment(BaseModel):
    """Currency assessment for an evidence artifact."""

    status: str = Field(
        ..., pattern="^(current|stale|unknown)$",
        description="Currency status."
    )
    detail: str = Field(
        ..., description="Details about the currency assessment."
    )


class AnalyzeEvidenceResponse(BaseModel):
    """Response schema for the evidence analysis endpoint."""

    relevance_scores: list[RelevanceScore] = Field(
        ..., description="Relevance scores for each control."
    )
    most_relevant_control: str = Field(
        ..., description="The control with the highest relevance score."
    )
    suggested_artifact_type: str = Field(
        ..., description="Suggested artifact type classification."
    )
    quality_assessment: str = Field(
        ..., pattern="^(Good|Fair|Poor)$",
        description="Overall quality assessment."
    )
    currency: CurrencyAssessment = Field(
        ..., description="Document currency assessment."
    )
    confidence: float = Field(
        ..., ge=0, le=1,
        description="Confidence level of the analysis (0.0-1.0)."
    )
    requires_review: bool = Field(
        ..., description="Whether this result needs human review."
    )


class SuggestMappingRequest(BaseModel):
    """Request schema for mapping suggestion endpoint."""

    evidence_id: str = Field(
        ..., description="UUID of the evidence artifact."
    )


class MappingSuggestion(BaseModel):
    """A single mapping suggestion."""

    control_id: str = Field(
        ..., description="Target control ID."
    )
    title: str = Field(
        ..., description="Control title."
    )
    confidence: float = Field(
        ..., ge=0, le=100,
        description="Confidence percentage."
    )
    suggested_artifact_type: str = Field(
        ..., description="Suggested artifact type for the mapping."
    )


class SuggestMappingResponse(BaseModel):
    """Response schema for mapping suggestion endpoint."""

    evidence_id: str = Field(
        ..., description="The analyzed evidence artifact ID."
    )
    evidence_name: str = Field(
        ..., description="The analyzed evidence artifact name."
    )
    suggestions: list[MappingSuggestion] = Field(
        ..., description="List of suggested mappings."
    )


# =============================================================================
# Helper Functions
# =============================================================================

def _create_audit_log(
    action: str,
    entity_type: str,
    entity_id: str,
    user_id: Optional[str] = None,
    new_values: Optional[dict[str, Any]] = None,
    ip_address: Optional[str] = None,
) -> None:
    """Create an audit log entry for an agent action.

    Args:
        action: The action type (AGENT_CHAT, AGENT_ANALYZE, AGENT_SUGGEST).
        entity_type: The entity type.
        entity_id: The entity ID.
        user_id: Optional user ID.
        new_values: Optional additional context.
        ip_address: Optional IP address.
    """
    try:
        from api.database import create_audit_log as db_audit

        db_audit(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            new_values=new_values or {},
            ip_address=ip_address,
        )
    except Exception:
        # Audit logging should never break the main flow
        pass


# =============================================================================
# Routes
# =============================================================================

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: Request,
    body: ChatRequest,
) -> dict[str, Any]:
    """Chat with the GRC compliance chatbot.

    Accepts a user message and returns a compliance-focused response
    from the GRC Chatbot Agent. The agent uses RAG to retrieve relevant
    NIST SP 800-53 information from the knowledge base.

    Returns a user-friendly error message if the AI service is unavailable.
    """
    if not config.enable_ai_chat:
        raise HTTPException(
            status_code=503,
            detail="AI chat is currently disabled.",
        )

    message = body.message.strip()
    if not message:
        raise HTTPException(
            status_code=422,
            detail="Message cannot be empty.",
        )

    # Get client IP for audit logging
    ip_address = request.client.host if request.client else None

    # Generate or reuse session ID
    session_id = body.session_id or str(uuid.uuid4())

    try:
        from agents import process_chat_message

        # Persist session in database
        from api.database import (
            get_agent_session,
            create_agent_session,
            update_agent_session,
        )

        existing_session = get_agent_session(session_id)
        if existing_session:
            # Update the existing session's context
            context = existing_session.get("context", {}) or {}
            messages = context.get("messages", [])
            messages.append({"role": "user", "content": message})
            update_agent_session(
                session_id=session_id,
                context={**context, "messages": messages},
            )
        else:
            # Create a new session
            create_agent_session(
                session_id=session_id,
                user_id=body.user_id,
                session_type="grc_chatbot",
                context={"messages": [{"role": "user", "content": message}]},
                memory_summary=f"Chat started: {message[:100]}...",
            )

        result = process_chat_message(
            message=message,
            user_id=body.user_id,
            session_id=session_id,
        )

        if "error" in result:
            # Log the guardrail block
            _create_audit_log(
                action="AGENT_CHAT_BLOCKED",
                entity_type="agent_chat",
                entity_id=session_id,
                user_id=body.user_id,
                new_values={
                    "reason": result["error"][:200],
                    "session_id": session_id,
                },
                ip_address=ip_address,
            )
            raise HTTPException(
                status_code=400,
                detail=result["error"],
            )

        # Update session with the response
        existing_session = get_agent_session(session_id)
        if existing_session:
            context = existing_session.get("context", {}) or {}
            messages = context.get("messages", [])
            messages.append({"role": "assistant", "content": result.get("response", "")})
            update_agent_session(
                session_id=session_id,
                context={**context, "messages": messages},
                memory_summary=messages[-1].get("content", "")[:200] if messages else "",
            )

        # Log successful chat interaction
        _create_audit_log(
            action="AGENT_CHAT",
            entity_type="agent_chat",
            entity_id=session_id,
            user_id=body.user_id,
            new_values={
                "session_id": session_id,
                "response_length": len(result.get("response", "")),
            },
            ip_address=ip_address,
        )

        return ChatResponse(
            response=result["response"],
            session_id=session_id,
        )

    except HTTPException:
        raise
    except Exception:
        # Log the error without exposing internals
        _create_audit_log(
            action="AGENT_CHAT_ERROR",
            entity_type="agent_chat",
            entity_id=session_id,
            user_id=body.user_id,
            ip_address=ip_address,
        )
        raise HTTPException(
            status_code=503,
            detail="The AI service is temporarily unavailable. Please try again later.",
        )


@router.post(
    "/analyze-evidence",
    response_model=AnalyzeEvidenceResponse,
)
async def analyze_evidence_endpoint(
    request: Request,
    body: AnalyzeEvidenceRequest,
) -> dict[str, Any]:
    """Analyze an uploaded evidence artifact for control relevance.

    Returns relevance scores for each of the 5 NIST SP 800-53 controls,
    suggested artifact type, quality assessment, and currency check.
    Low-confidence results are flagged for human review.
    """
    try:
        from api.database import get_evidence

        evidence = get_evidence(body.evidence_id)
        if not evidence:
            raise HTTPException(
                status_code=404,
                detail=f"Evidence artifact '{body.evidence_id}' not found.",
            )

        from agents import analyze_evidence as analyze

        result = analyze(
            name=evidence.get("name", "Unknown"),
            content_text=evidence.get("content_text"),
            file_type=evidence.get("file_type"),
            uploaded_at=evidence.get("uploaded_at"),
            use_llm=config.enable_ai_chat,
        )

        # Format relevance scores
        scores_list = [
            RelevanceScore(
                control_id=cid,
                score=result["relevance_scores"].get(cid, 0.0),
            )
            for cid in ["PE-03", "AC-02", "SC-07", "IR-06", "RA-05"]
        ]

        # Log the analysis
        ip_address = request.client.host if request.client else None
        _create_audit_log(
            action="AGENT_ANALYZE",
            entity_type="evidence_artifact",
            entity_id=body.evidence_id,
            new_values={
                "most_relevant_control": result.get("most_relevant_control"),
                "confidence": result.get("confidence"),
                "requires_review": result.get("requires_review"),
            },
            ip_address=ip_address,
        )

        return AnalyzeEvidenceResponse(
            relevance_scores=scores_list,
            most_relevant_control=result.get(
                "most_relevant_control", "PE-03"
            ),
            suggested_artifact_type=result.get(
                "suggested_artifact_type", "Documentation"
            ),
            quality_assessment=result.get("quality_assessment", "Fair"),
            currency=CurrencyAssessment(
                status=result.get("currency", {}).get("status", "unknown"),
                detail=result.get("currency", {}).get(
                    "detail", "Unable to assess."
                ),
            ),
            confidence=result.get("confidence", 0.0),
            requires_review=result.get("requires_review", True),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing evidence: {str(e)}",
        )


@router.post(
    "/suggest-mapping",
    response_model=SuggestMappingResponse,
)
async def suggest_mapping_endpoint(
    request: Request,
    body: SuggestMappingRequest,
) -> dict[str, Any]:
    """Suggest control mappings for an evidence artifact.

    Analyzes the evidence content and suggests which controls it
    maps to, along with confidence levels and recommended artifact types.
    """
    try:
        from api.database import get_evidence

        evidence = get_evidence(body.evidence_id)
        if not evidence:
            raise HTTPException(
                status_code=404,
                detail=f"Evidence artifact '{body.evidence_id}' not found.",
            )

        from agents.tools import GRCTools

        tools = GRCTools()
        suggestion_text = tools.suggest_mapping(body.evidence_id)

        # Parse the suggestion text into structured data
        suggestions: list[MappingSuggestion] = []
        from api.database import get_cursor

        with get_cursor() as cur:
            cur.execute(
                "SELECT id, control_id, title FROM controls ORDER BY control_id"
            )
            all_controls = cur.fetchall()

        content_text = evidence.get("content_text", "") or ""
        content_lower = content_text.lower()
        evidence_name = evidence.get("name", "Unknown")

        keyword_map = {
            "PE-03": [
                "physical", "access", "badge", "visitor", "security",
                "door", "entry", "exit", "perimeter", "facility",
            ],
            "AC-02": [
                "account", "password", "user", "authentication",
                "privilege", "iam", "identity", "active directory",
                "ldap", "mfa", "login",
            ],
            "SC-07": [
                "network", "firewall", "boundary", "segmentation",
                "vlan", "dmz", "ids", "ips", "traffic", "subnet",
            ],
            "IR-06": [
                "incident", "response", "breach", "reporting",
                "escalation", "emergency", "compromise", "crisis",
            ],
            "RA-05": [
                "vulnerability", "scan", "remediation", "patch",
                "nessus", "cve", "risk assessment", "audit",
            ],
        }

        for ctrl in all_controls:
            ctrl_ref = ctrl["control_id"]
            keywords = keyword_map.get(ctrl_ref, [])
            matches = sum(1 for kw in keywords if kw in content_lower)

            if matches > 0:
                confidence = min(matches / len(keywords) * 100, 95)
                requirements = ctrl.get("artifact_requirements") or []
                suggested_type = "Documentation"
                if requirements and isinstance(requirements, list):
                    suggested_type = requirements[0].get(
                        "type", "Documentation"
                    )

                suggestions.append(
                    MappingSuggestion(
                        control_id=ctrl_ref,
                        title=ctrl["title"],
                        confidence=round(confidence, 1),
                        suggested_artifact_type=suggested_type,
                    )
                )

        # Sort by confidence descending
        suggestions.sort(key=lambda s: s.confidence, reverse=True)

        # Log the suggestion
        ip_address = request.client.host if request.client else None
        _create_audit_log(
            action="AGENT_SUGGEST",
            entity_type="evidence_artifact",
            entity_id=body.evidence_id,
            new_values={
                "suggestion_count": len(suggestions),
                "top_suggestion": suggestions[0].control_id if suggestions else None,
            },
            ip_address=ip_address,
        )

        return SuggestMappingResponse(
            evidence_id=body.evidence_id,
            evidence_name=evidence_name,
            suggestions=suggestions,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error suggesting mapping: {str(e)}",
        )


# =============================================================================
# Agent Session Endpoints
# =============================================================================


class SessionListItem(BaseModel):
    """Schema for a session list item."""

    id: str
    user_id: Optional[str] = None
    session_type: str = "grc_chatbot"
    memory_summary: Optional[str] = None
    started_at: Optional[str] = None
    messages: list[dict[str, Any]] = []


class SessionDetailResponse(BaseModel):
    """Schema for session detail with full context."""

    id: str
    user_id: Optional[str] = None
    session_type: str = "grc_chatbot"
    memory_summary: Optional[str] = None
    started_at: Optional[str] = None
    messages: list[dict[str, Any]] = []


class SessionListResponse(BaseModel):
    """Schema for session list response."""

    items: list[SessionListItem]
    total: int


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions_endpoint(
    request: Request,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """List all agent chat sessions.

    Returns a list of previous chat sessions, most recent first,
    for the session list/resume functionality.
    """
    try:
        from api.database import list_agent_sessions, count_agent_sessions

        sessions = list_agent_sessions(limit=limit, offset=offset)
        total = count_agent_sessions()

        items = [
            SessionListItem(
                id=s["id"],
                user_id=s.get("user_id"),
                session_type=s.get("session_type", "grc_chatbot"),
                memory_summary=s.get("memory_summary", ""),
                started_at=s.get("started_at"),
            )
            for s in sessions
        ]

        return SessionListResponse(items=items, total=total)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing sessions: {str(e)}",
        )


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session_endpoint(
    request: Request,
    session_id: str,
) -> dict[str, Any]:
    """Get a single agent session by ID.

    Used to resume a specific chat session and retrieve its context.
    """
    try:
        from api.database import get_agent_session

        session = get_agent_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session '{session_id}' not found.",
            )

        context = session.get("context", {}) or {}
        messages = context.get("messages", [])

        return SessionDetailResponse(
            id=session["id"],
            user_id=session.get("user_id"),
            session_type=session.get("session_type", "grc_chatbot"),
            memory_summary=session.get("memory_summary", ""),
            started_at=session.get("started_at"),
            messages=messages,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting session: {str(e)}",
        )


@router.delete("/sessions/{session_id}")
async def delete_session_endpoint(
    request: Request,
    session_id: str,
) -> dict[str, Any]:
    """Delete an agent session.

    Removes the session and its associated context from the database.
    """
    try:
        from api.database import delete_agent_session

        deleted = delete_agent_session(session_id)
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"Session '{session_id}' not found.",
            )

        return {"deleted": True, "session_id": session_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting session: {str(e)}",
        )
