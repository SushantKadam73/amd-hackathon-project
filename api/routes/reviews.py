"""GRC Platform - Review Workflow API Routes.

Endpoints for submitting, listing, approving, and rejecting reviews.
Implements strict state transitions and self-approval prevention.
"""

from fastapi import APIRouter, HTTPException, Request

from api.database import (
    approve_review,
    create_review,
    get_review,
    list_reviews,
    reject_review,
)
from api.models import (
    ErrorResponse,
    ReviewActionRequest,
    ReviewActionRequestReject,
    ReviewCreate,
    ReviewListResponse,
    ReviewResponse,
)

router = APIRouter(prefix="/api/v1/reviews", tags=["Reviews"])


@router.get(
    "",
    response_model=ReviewListResponse,
    summary="List all review workflows",
)
async def get_reviews() -> ReviewListResponse:
    """Retrieve all review workflow entries.

    Returns reviews sorted by creation date (newest first).
    """
    try:
        reviews = list_reviews()
        items = [
            ReviewResponse(
                id=r["id"],
                entity_type=r["entity_type"],
                entity_id=r["entity_id"],
                workflow_status=r["workflow_status"],
                submitted_by=r.get("submitted_by"),
                reviewed_by=r.get("reviewed_by"),
                review_notes=r.get("review_notes"),
                created_at=r.get("created_at"),
                updated_at=r.get("updated_at"),
                submitted_by_username=r.get("submitted_by_username"),
                reviewed_by_username=r.get("reviewed_by_username"),
            )
            for r in reviews
        ]
        return ReviewListResponse(items=items, total=len(items))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve reviews: {str(e)}",
        )


@router.post(
    "",
    response_model=ReviewResponse,
    status_code=201,
    responses={
        201: {"description": "Review created"},
        422: {"description": "Validation error", "model": ErrorResponse},
    },
    summary="Submit for review",
)
async def submit_for_review(
    body: ReviewCreate,
    request: Request,
) -> ReviewResponse:
    """Submit an entity for review.

    Creates a review workflow record with status 'pending'.
    An audit log entry is created automatically.
    """
    try:
        client_ip = request.client.host if request.client else None
        review = create_review(
            entity_type=body.entity_type,
            entity_id=body.entity_id,
            submitted_by=None,  # Will be enhanced with auth
            review_notes=body.review_notes,
            ip_address=client_ip,
        )
        return ReviewResponse(
            id=review["id"],
            entity_type=review["entity_type"],
            entity_id=review["entity_id"],
            workflow_status=review["workflow_status"],
            submitted_by=review.get("submitted_by"),
            reviewed_by=review.get("reviewed_by"),
            review_notes=review.get("review_notes"),
            created_at=review.get("created_at"),
            updated_at=review.get("updated_at"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create review: {str(e)}",
        )


@router.put(
    "/{review_id}/approve",
    response_model=ReviewResponse,
    responses={
        200: {"description": "Review approved"},
        403: {"description": "Self-approval not allowed", "model": ErrorResponse},
        404: {"description": "Review not found", "model": ErrorResponse},
        409: {"description": "Review already processed", "model": ErrorResponse},
        422: {"description": "Validation error", "model": ErrorResponse},
    },
    summary="Approve a review",
)
async def approve_review_endpoint(
    review_id: str,
    body: ReviewActionRequest,
    request: Request,
) -> ReviewResponse:
    """Approve a pending review.

    Changes workflow_status to 'approved' and updates the underlying
    entity status. Self-approval is not allowed (returns 403).
    Already processed reviews return 409 Conflict.
    """
    try:
        review = get_review(review_id)
        if not review:
            raise HTTPException(
                status_code=404,
                detail=f"Review with id '{review_id}' not found",
            )

        # Check self-approval prevention
        if review.get("submitted_by") and review["submitted_by"] == body.reviewer_id:
            raise HTTPException(
                status_code=403,
                detail="Cannot approve your own submission",
            )

        # Check state transitions - only pending can be approved
        if review["workflow_status"] != "pending":
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Cannot approve review with status "
                    f"'{review['workflow_status']}'. "
                    f"Only pending reviews can be approved."
                ),
            )

        client_ip = request.client.host if request.client else None
        updated = approve_review(
            review_id=review_id,
            reviewed_by=body.reviewer_id,
            review_notes=body.review_notes,
            ip_address=client_ip,
        )

        if not updated:
            raise HTTPException(
                status_code=409,
                detail="Review has already been processed",
            )

        return ReviewResponse(
            id=updated["id"],
            entity_type=updated["entity_type"],
            entity_id=updated["entity_id"],
            workflow_status=updated["workflow_status"],
            submitted_by=updated.get("submitted_by"),
            reviewed_by=updated.get("reviewed_by"),
            review_notes=updated.get("review_notes"),
            created_at=updated.get("created_at"),
            updated_at=updated.get("updated_at"),
            submitted_by_username=updated.get("submitted_by_username"),
            reviewed_by_username=updated.get("reviewed_by_username"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to approve review: {str(e)}",
        )


@router.put(
    "/{review_id}/reject",
    response_model=ReviewResponse,
    responses={
        200: {"description": "Review rejected"},
        404: {"description": "Review not found", "model": ErrorResponse},
        409: {"description": "Review already processed", "model": ErrorResponse},
        422: {"description": "Review notes required", "model": ErrorResponse},
    },
    summary="Reject a review",
)
async def reject_review_endpoint(
    review_id: str,
    body: ReviewActionRequestReject,
    request: Request,
) -> ReviewResponse:
    """Reject a pending review.

    Requires review_notes (non-empty). Changes workflow_status to 'rejected'
    and updates the underlying entity status.
    """
    try:
        review = get_review(review_id)
        if not review:
            raise HTTPException(
                status_code=404,
                detail=f"Review with id '{review_id}' not found",
            )

        # Check state transitions - only pending can be rejected
        if review["workflow_status"] != "pending":
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Cannot reject review with status "
                    f"'{review['workflow_status']}'. "
                    f"Only pending reviews can be rejected."
                ),
            )

        client_ip = request.client.host if request.client else None
        updated = reject_review(
            review_id=review_id,
            reviewed_by=body.reviewer_id,
            review_notes=body.review_notes,
            ip_address=client_ip,
        )

        if not updated:
            raise HTTPException(
                status_code=409,
                detail="Review has already been processed",
            )

        return ReviewResponse(
            id=updated["id"],
            entity_type=updated["entity_type"],
            entity_id=updated["entity_id"],
            workflow_status=updated["workflow_status"],
            submitted_by=updated.get("submitted_by"),
            reviewed_by=updated.get("reviewed_by"),
            review_notes=updated.get("review_notes"),
            created_at=updated.get("created_at"),
            updated_at=updated.get("updated_at"),
            submitted_by_username=updated.get("submitted_by_username"),
            reviewed_by_username=updated.get("reviewed_by_username"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reject review: {str(e)}",
        )
