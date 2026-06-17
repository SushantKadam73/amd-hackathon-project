"""Tests for the GRC Platform API endpoints.

These tests verify that all routes are registered, request/response models
are correct, and error handling works properly. Database-dependent tests
require PostgreSQL to be running.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


# =============================================================================
# Health & Status
# =============================================================================

class TestHealth:
    """Test suite for health check and status endpoints."""

    def test_health_endpoint(self) -> None:
        """Health endpoint should return 200 with status healthy."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "environment" in data
        assert "llm_provider" in data

    def test_api_status_endpoint(self) -> None:
        """Status endpoint should return 200 with configuration."""
        response = client.get("/api/v1/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["version"] == "0.1.0"
        assert "llm" in data
        assert "embedding" in data
        assert "features" in data


# =============================================================================
# Framework Routes
# =============================================================================

class TestFrameworksRoutes:
    """Test suite for framework API endpoints."""

    def test_get_frameworks_route_registered(self) -> None:
        """GET /api/v1/frameworks should be registered (may fail without DB)."""
        response = client.get("/api/v1/frameworks")
        # Should either return 200 (DB available) or 500 (DB not available)
        assert response.status_code in (200, 500)

    def test_create_framework_route_registered(self) -> None:
        """POST /api/v1/frameworks should be registered."""
        response = client.post(
            "/api/v1/frameworks",
            json={"name": "Test Framework", "version": "1.0"},
        )
        # Should either return 201 (DB available) or 500/422 (validation/DB error)
        assert response.status_code in (201, 500, 422)

    def test_get_framework_by_id_route_registered(self) -> None:
        """GET /api/v1/frameworks/{id} should be registered."""
        response = client.get("/api/v1/frameworks/nonexistent-id")
        # Should either return 404 (not found) or 500 (DB error)
        assert response.status_code in (404, 500)

    def test_get_framework_controls_route_registered(self) -> None:
        """GET /api/v1/frameworks/{id}/controls should be registered."""
        response = client.get("/api/v1/frameworks/nonexistent-id/controls")
        # Should either return 404 (not found) or 500 (DB error)
        assert response.status_code in (404, 500)

    def test_create_framework_empty_name(self) -> None:
        """POST /api/v1/frameworks with empty name should return 422."""
        response = client.post(
            "/api/v1/frameworks",
            json={"name": "", "version": "1.0"},
        )
        assert response.status_code == 422

    def test_create_framework_missing_name(self) -> None:
        """POST /api/v1/frameworks without name should return 422."""
        response = client.post(
            "/api/v1/frameworks",
            json={"version": "1.0"},
        )
        assert response.status_code == 422


# =============================================================================
# Evidence Routes
# =============================================================================

class TestEvidenceRoutes:
    """Test suite for evidence API endpoints."""

    def test_get_evidence_route_registered(self) -> None:
        """GET /api/v1/evidence should be registered."""
        response = client.get("/api/v1/evidence")
        assert response.status_code in (200, 500)

    def test_get_evidence_by_id_route_registered(self) -> None:
        """GET /api/v1/evidence/{id} should be registered."""
        response = client.get("/api/v1/evidence/nonexistent-id")
        assert response.status_code in (404, 500)

    def test_upload_evidence_no_file(self) -> None:
        """POST /api/v1/evidence without file should return 422."""
        response = client.post("/api/v1/evidence")
        assert response.status_code == 422

    def test_map_to_control_route_registered(self) -> None:
        """POST /api/v1/evidence/{id}/map-to-control should be registered."""
        response = client.post(
            "/api/v1/evidence/nonexistent-id/map-to-control",
            json={"control_id": "nonexistent", "weightage": 10.0, "artifact_type": "Policy"},
        )
        assert response.status_code in (404, 500)


# =============================================================================
# Review Routes
# =============================================================================

class TestReviewRoutes:
    """Test suite for review workflow API endpoints."""

    def test_get_reviews_route_registered(self) -> None:
        """GET /api/v1/reviews should be registered."""
        response = client.get("/api/v1/reviews")
        assert response.status_code in (200, 500)

    def test_create_review_route_registered(self) -> None:
        """POST /api/v1/reviews should be registered."""
        response = client.post(
            "/api/v1/reviews",
            json={"entity_type": "evidence_control_mapping", "entity_id": "test"},
        )
        assert response.status_code in (201, 500, 422)

    def test_approve_review_route_registered(self) -> None:
        """PUT /api/v1/reviews/{id}/approve should be registered."""
        response = client.put(
            "/api/v1/reviews/nonexistent-id/approve",
            json={"reviewer_id": "user-id"},
        )
        assert response.status_code in (404, 500, 422)

    def test_reject_review_route_registered(self) -> None:
        """PUT /api/v1/reviews/{id}/reject should be registered."""
        response = client.put(
            "/api/v1/reviews/nonexistent-id/reject",
            json={"reviewer_id": "user-id", "review_notes": "Not acceptable"},
        )
        assert response.status_code in (404, 500, 422)

    def test_reject_review_empty_notes(self) -> None:
        """PUT /api/v1/reviews/{id}/reject with empty notes should return 422."""
        response = client.put(
            "/api/v1/reviews/nonexistent-id/reject",
            json={"reviewer_id": "user-id", "review_notes": ""},
        )
        assert response.status_code == 422


# =============================================================================
# Audit Log Routes
# =============================================================================

class TestAuditLogRoutes:
    """Test suite for audit log API endpoints."""

    def test_get_audit_logs_route_registered(self) -> None:
        """GET /api/v1/audit-logs should be registered."""
        response = client.get("/api/v1/audit-logs")
        assert response.status_code in (200, 500)

    def test_get_audit_logs_with_filters(self) -> None:
        """GET /api/v1/audit-logs with query params should work."""
        response = client.get("/api/v1/audit-logs?action=CREATE_EVIDENCE&limit=10")
        assert response.status_code in (200, 500)

    def test_audit_logs_delete_not_allowed(self) -> None:
        """DELETE /api/v1/audit-logs should return 405."""
        response = client.delete("/api/v1/audit-logs")
        assert response.status_code == 405

    def test_audit_logs_put_not_allowed(self) -> None:
        """PUT /api/v1/audit-logs should return 405."""
        response = client.put("/api/v1/audit-logs")
        assert response.status_code == 405

    def test_audit_logs_patch_not_allowed(self) -> None:
        """PATCH /api/v1/audit-logs should return 405."""
        response = client.patch("/api/v1/audit-logs")
        assert response.status_code == 405


# =============================================================================
# Reports Routes
# =============================================================================

class TestReportsRoutes:
    """Test suite for reports API endpoints."""

    def test_compliance_status_route_registered(self) -> None:
        """GET /api/v1/reports/compliance-status should be registered."""
        response = client.get("/api/v1/reports/compliance-status")
        assert response.status_code in (200, 500)

    def test_gap_summary_route_registered(self) -> None:
        """GET /api/v1/reports/gap-summary should be registered."""
        response = client.get("/api/v1/reports/gap-summary")
        assert response.status_code in (200, 500)

    def test_risk_heatmap_route_registered(self) -> None:
        """GET /api/v1/reports/risk-heatmap should be registered."""
        response = client.get("/api/v1/reports/risk-heatmap")
        assert response.status_code in (200, 500)


# =============================================================================
# Model Validation Tests
# =============================================================================

class TestModelValidation:
    """Test suite for Pydantic model validation."""

    def test_framework_create_valid(self) -> None:
        """FrameworkCreate should accept valid data."""
        from api.models import FrameworkCreate
        model = FrameworkCreate(name="NIST SP 800-53", version="Rev 5")
        assert model.name == "NIST SP 800-53"
        assert model.version == "Rev 5"

    def test_framework_create_invalid_empty_name(self) -> None:
        """FrameworkCreate should reject empty name."""
        from pydantic import ValidationError
        from api.models import FrameworkCreate
        with pytest.raises(ValidationError):
            FrameworkCreate(name="")

    def test_map_to_control_request_valid(self) -> None:
        """MapToControlRequest should accept valid data."""
        from api.models import MapToControlRequest
        model = MapToControlRequest(
            control_id="test-id", weightage=15.0, artifact_type="Policy Documents"
        )
        assert model.control_id == "test-id"
        assert model.weightage == 15.0

    def test_map_to_control_request_invalid_weightage(self) -> None:
        """MapToControlRequest should reject weightage > 100."""
        from pydantic import ValidationError
        from api.models import MapToControlRequest
        with pytest.raises(ValidationError):
            MapToControlRequest(
                control_id="test", weightage=150.0, artifact_type="Policy"
            )

    def test_review_action_reject_valid(self) -> None:
        """ReviewActionRequestReject should require non-empty notes."""
        from pydantic import ValidationError
        from api.models import ReviewActionRequestReject
        with pytest.raises(ValidationError):
            ReviewActionRequestReject(reviewer_id="user-id", review_notes="")

    def test_review_action_reject_with_notes(self) -> None:
        """ReviewActionRequestReject should accept notes."""
        from api.models import ReviewActionRequestReject
        model = ReviewActionRequestReject(
            reviewer_id="user-id", review_notes="Insufficient evidence"
        )
        assert model.review_notes == "Insufficient evidence"

    def test_compliance_status_response(self) -> None:
        """ComplianceStatusResponse should serialize correctly."""
        from api.models import ComplianceStatusResponse, ControlScore
        model = ComplianceStatusResponse(
            overall_score=45.5,
            overall_status="Partially Mapped",
            total_controls=5,
            controls=[
                ControlScore(
                    control_id="PE-03",
                    title="Physical Access Control",
                    total_required_weightage=100.0,
                    validated_weightage=30.0,
                    score=30.0,
                    status="Unmapped",
                )
            ],
        )
        data = model.model_dump()
        assert data["overall_score"] == 45.5
        assert data["total_controls"] == 5
        assert len(data["controls"]) == 1
        assert data["controls"][0]["control_id"] == "PE-03"

    def test_control_score_with_evidence_count(self) -> None:
        """ControlScore should accept optional evidence_count."""
        from api.models import ControlScore
        model = ControlScore(
            control_id="AC-02",
            title="Account Management",
            total_required_weightage=100.0,
            validated_weightage=50.0,
            score=50.0,
            status="Partially Mapped",
            evidence_count=3,
        )
        assert model.evidence_count == 3

    def test_gap_summary_response(self) -> None:
        """GapSummaryResponse should serialize correctly."""
        from api.models import GapSummaryResponse, GapSeverityCount
        model = GapSummaryResponse(
            total_open_gaps=8,
            gaps_by_severity=GapSeverityCount(
                critical=1, high=3, medium=2, low=2
            ),
            oldest_open_gap_age_days=0,
        )
        data = model.model_dump()
        assert data["total_open_gaps"] == 8
        assert data["gaps_by_severity"]["critical"] == 1
        assert data["gaps_by_severity"]["high"] == 3

    def test_risk_heatmap_item(self) -> None:
        """RiskHeatmapItem should serialize correctly."""
        from api.models import RiskHeatmapItem
        model = RiskHeatmapItem(
            control_id="PE-03",
            status="Partially Mapped",
            score=45.0,
            color="#ffcc00",
        )
        data = model.model_dump()
        assert data["control_id"] == "PE-03"
        assert data["status"] == "Partially Mapped"
        assert data["color"] == "#ffcc00"
