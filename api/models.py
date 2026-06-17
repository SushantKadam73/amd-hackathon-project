"""GRC Platform - Pydantic Models for API Request/Response Schemas.

Provides data validation, serialization, and documentation for all API endpoints.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Framework Models
# =============================================================================

class FrameworkCreate(BaseModel):
    """Schema for creating a new compliance framework."""

    name: str = Field(..., min_length=1, max_length=255, description="Framework name")
    version: Optional[str] = Field(None, max_length=50, description="Version string")
    description: Optional[str] = Field(None, description="Framework description")


class FrameworkResponse(BaseModel):
    """Schema for framework response."""

    id: str
    name: str
    version: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


class FrameworkListResponse(BaseModel):
    """Schema for list of frameworks."""

    items: list[FrameworkResponse]
    total: int


# =============================================================================
# Control Models
# =============================================================================

class ArtifactRequirement(BaseModel):
    """Schema for a required artifact type with weightage."""

    type: str = Field(..., alias="type", description="Artifact type name")
    weightage: float = Field(..., ge=0, le=100, description="Weightage percentage")
    description: Optional[str] = Field(None, description="Description of the artifact type")

    model_config = {"populate_by_name": True, "from_attributes": True}


class CrossFrameworkMapping(BaseModel):
    """Schema for a cross-framework mapping."""

    mapped_to: str = Field(..., description="Mapped control/framework reference")
    description: Optional[str] = Field(None, description="Mapping description")


class CrossFrameworkMappings(BaseModel):
    """Schema for all cross-framework mappings of a control."""

    nist_csf_2_0: Optional[CrossFrameworkMapping] = Field(None, alias="nist_csf_2_0")
    cis_controls_v8: Optional[CrossFrameworkMapping] = Field(None, alias="cis_controls_v8")
    pci_dss_v4_0_1: Optional[CrossFrameworkMapping] = Field(None, alias="pci_dss_v4_0_1")

    model_config = {"populate_by_name": True, "from_attributes": True}


class ControlResponse(BaseModel):
    """Schema for control response."""

    id: str
    framework_id: str
    control_id: str
    title: str
    description: Optional[str] = None
    control_family: Optional[str] = None
    priority: Optional[str] = "medium"
    artifact_requirements: Optional[list[dict[str, Any]]] = None
    cross_framework_mappings: Optional[dict[str, Any]] = None

    model_config = {"from_attributes": True}


class ControlListResponse(BaseModel):
    """Schema for list of controls."""

    items: list[ControlResponse]
    total: int


# =============================================================================
# Evidence Models
# =============================================================================

class EvidenceResponse(BaseModel):
    """Schema for evidence artifact response."""

    id: str
    name: str
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    checksum: Optional[str] = None
    content_text: Optional[str] = None
    uploaded_by: Optional[str] = None
    uploaded_at: Optional[str] = None

    model_config = {"from_attributes": True}


class EvidenceListResponse(BaseModel):
    """Schema for list of evidence artifacts."""

    items: list[EvidenceResponse]
    total: int


class MapToControlRequest(BaseModel):
    """Schema for mapping evidence to a control."""

    control_id: str = Field(..., description="UUID of the target control")
    weightage: float = Field(..., ge=0, le=100, description="Weightage percentage for this artifact type")
    artifact_type: str = Field(..., min_length=1, description="Type of artifact (e.g., 'Policy Documents')")


class MapToControlResponse(BaseModel):
    """Schema for mapping response."""

    id: str
    evidence_id: str
    control_id: str
    weightage: float
    artifact_type: str
    mapping_status: str
    mapped_at: Optional[str] = None


class EvidenceMappingResponse(BaseModel):
    """Schema for evidence mapping with control details."""

    id: str
    evidence_id: str
    control_id: str
    control_ref_id: Optional[str] = None
    control_title: Optional[str] = None
    weightage: float
    artifact_type: str
    mapping_status: str
    mapped_at: Optional[str] = None

    model_config = {"from_attributes": True}


class EvidenceMappingListResponse(BaseModel):
    """Schema for list of evidence mappings."""

    items: list[EvidenceMappingResponse]
    total: int


# =============================================================================
# Review Models
# =============================================================================

class ReviewCreate(BaseModel):
    """Schema for creating a review workflow."""

    entity_type: str = Field(..., description="Type of entity being reviewed")
    entity_id: str = Field(..., description="UUID of the entity")
    review_notes: Optional[str] = Field(None, description="Initial review notes")


class ReviewResponse(BaseModel):
    """Schema for review workflow response."""

    id: str
    entity_type: str
    entity_id: str
    workflow_status: str
    submitted_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    submitted_by_username: Optional[str] = None
    reviewed_by_username: Optional[str] = None

    model_config = {"from_attributes": True}


class ReviewListResponse(BaseModel):
    """Schema for list of reviews."""

    items: list[ReviewResponse]
    total: int


class ReviewActionRequest(BaseModel):
    """Schema for approve/reject actions on a review."""

    reviewer_id: str = Field(..., description="UUID of the reviewer")
    review_notes: Optional[str] = Field(None, description="Notes for the action")


class ReviewActionRequestReject(BaseModel):
    """Schema for reject action with required notes."""

    reviewer_id: str = Field(..., description="UUID of the reviewer")
    review_notes: str = Field(..., min_length=1, description="Required rejection notes")

    @field_validator("review_notes")
    @classmethod
    def notes_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Review notes are required for rejection")
        return v.strip()


# =============================================================================
# Audit Log Models
# =============================================================================

class AuditLogResponse(BaseModel):
    """Schema for audit log entry response."""

    id: str
    user_id: Optional[str] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    old_values: Optional[Any] = None
    new_values: Optional[Any] = None
    ip_address: Optional[str] = None
    created_at: Optional[str] = None
    user_username: Optional[str] = None

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    """Schema for list of audit log entries."""

    items: list[AuditLogResponse]
    total: int


# =============================================================================
# Compliance Score Models
# =============================================================================

class ControlScore(BaseModel):
    """Schema for a single control's compliance score."""

    control_id: str
    title: str
    total_required_weightage: float
    validated_weightage: float
    score: float
    status: str
    evidence_count: int = 0


class ComplianceStatusResponse(BaseModel):
    """Schema for compliance status report."""

    overall_score: float
    overall_status: str
    total_controls: int
    controls: list[ControlScore]


# =============================================================================
# Gap Summary Models
# =============================================================================

class GapSeverityCount(BaseModel):
    """Schema for gap count by severity."""

    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0


class GapSummaryResponse(BaseModel):
    """Schema for gap summary report."""

    total_open_gaps: int
    gaps_by_severity: GapSeverityCount
    oldest_open_gap_age_days: int = 0


# =============================================================================
# Risk Heatmap Models
# =============================================================================

class RiskHeatmapItem(BaseModel):
    """Schema for a single risk heatmap data point."""

    control_id: str
    status: str
    score: float
    color: str


class RiskHeatmapResponse(BaseModel):
    """Schema for risk heatmap response."""

    items: list[RiskHeatmapItem]


# =============================================================================
# User Models
# =============================================================================

class UserResponse(BaseModel):
    """Schema for user response."""

    id: str
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: bool = True
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


# =============================================================================
# Generic Error Models
# =============================================================================

class ErrorResponse(BaseModel):
    """Schema for error responses."""

    detail: str
    error_code: Optional[str] = None
    errors: Optional[list[dict[str, Any]]] = None
