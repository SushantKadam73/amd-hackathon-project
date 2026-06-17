"""GRC Platform - Reports API Routes.

Endpoints for compliance status, gap analysis, and other reports.
"""

from fastapi import APIRouter, HTTPException

from api.database import (
    calculate_compliance_score,
    get_gap_summary,
    get_risk_heatmap,
)
from api.models import (
    ComplianceStatusResponse,
    ControlScore,
    GapSeverityCount,
    GapSummaryResponse,
    RiskHeatmapItem,
    RiskHeatmapResponse,
)

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


@router.get(
    "/compliance-status",
    response_model=ComplianceStatusResponse,
    responses={
        200: {"description": "Compliance status report"},
    },
    summary="Get compliance status report",
)
async def get_compliance_status() -> ComplianceStatusResponse:
    """Calculate and return the compliance status across all controls.

    The compliance score is calculated as:
    - Each control's score = (validated evidence weightage / total required weightage) * 100
    - Overall score = average of all control scores

    Only approved evidence-control mappings count toward the score.
    """
    try:
        result = calculate_compliance_score()

        controls = [
            ControlScore(
                control_id=c["control_id"],
                title=c["title"],
                total_required_weightage=c["total_required_weightage"],
                validated_weightage=c["validated_weightage"],
                score=c["score"],
                status=c["status"],
                evidence_count=c.get("evidence_count", 0),
            )
            for c in result["controls"]
        ]

        return ComplianceStatusResponse(
            overall_score=result["overall_score"],
            overall_status=result["overall_status"],
            total_controls=result["total_controls"],
            controls=controls,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate compliance status: {str(e)}",
        )


@router.get(
    "/gap-summary",
    response_model=GapSummaryResponse,
    responses={
        200: {"description": "Gap summary report"},
    },
    summary="Get gap summary report",
)
async def get_gap_summary_endpoint() -> GapSummaryResponse:
    """Return a summary of open gaps across all controls.

    Gaps are required artifact types without approved evidence mappings.
    Severity is based on weightage.
    """
    try:
        result = get_gap_summary()
        severity = result.get("gaps_by_severity", {})
        return GapSummaryResponse(
            total_open_gaps=result.get("total_open_gaps", 0),
            gaps_by_severity=GapSeverityCount(
                critical=severity.get("critical", 0),
                high=severity.get("high", 0),
                medium=severity.get("medium", 0),
                low=severity.get("low", 0),
            ),
            oldest_open_gap_age_days=result.get("oldest_open_gap_age_days", 0),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate gap summary: {str(e)}",
        )


@router.get(
    "/risk-heatmap",
    response_model=RiskHeatmapResponse,
    responses={
        200: {"description": "Risk heatmap data"},
    },
    summary="Get risk heatmap data",
)
async def get_risk_heatmap_endpoint() -> RiskHeatmapResponse:
    """Return risk heatmap data for all controls.

    Returns per-control status with color coding for heatmap visualization.
    """
    try:
        items = get_risk_heatmap()
        return RiskHeatmapResponse(
            items=[
                RiskHeatmapItem(
                    control_id=item["control_id"],
                    status=item["status"],
                    score=item["score"],
                    color=item["color"],
                )
                for item in items
            ],
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate risk heatmap: {str(e)}",
        )
