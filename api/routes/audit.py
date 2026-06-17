"""GRC Platform - Audit Log API Routes.

Endpoints for querying audit log entries. Audit logs are INSERT-only
and immutable - no update or delete endpoints are exposed.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from api.database import list_audit_logs
from api.models import AuditLogListResponse, AuditLogResponse, ErrorResponse

router = APIRouter(prefix="/api/v1/audit-logs", tags=["Audit"])


@router.api_route(
    "",
    methods=["DELETE", "PUT", "PATCH"],
    include_in_schema=False,
)
async def audit_logs_method_not_allowed() -> None:
    """Return 405 for unsupported methods on audit logs.

    Audit logs are immutable and INSERT-only.
    """
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=405,
        content={"detail": "Method Not Allowed. Audit logs are immutable and INSERT-only."},
    )


@router.get(
    "",
    response_model=AuditLogListResponse,
    responses={
        200: {"description": "List of audit log entries"},
        405: {"description": "Method not allowed for other HTTP methods"},
    },
    summary="List audit log entries",
)
async def get_audit_logs(
    action: Optional[str] = Query(None, description="Filter by action type (single, legacy)"),
    actions: Optional[str] = Query(None, description="Filter by action types (comma-separated, multi-select)"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    date_from: Optional[str] = Query(None, description="Filter from date (ISO format, inclusive)"),
    date_to: Optional[str] = Query(None, description="Filter to date (ISO format, inclusive)"),
    entity_id_search: Optional[str] = Query(None, description="Search entity ID (partial match)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
) -> AuditLogListResponse:
    """Retrieve audit log entries.

    Returns entries in reverse chronological order with optional filtering
    by action type (single or multi), user, date range, and entity ID search.
    Supports pagination with limit and offset.

    Note: Audit logs are immutable and INSERT-only. DELETE, PUT, and PATCH
    methods are not supported on this endpoint.
    """
    try:
        # Parse comma-separated actions into list
        action_list: Optional[list[str]] = None
        if actions:
            action_list = [a.strip() for a in actions.split(",") if a.strip()]

        logs = list_audit_logs(
            action=action,
            actions=action_list,
            entity_type=entity_type,
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
            entity_id_search=entity_id_search,
            limit=limit,
            offset=offset,
        )
        items = [
            AuditLogResponse(
                id=log["id"],
                user_id=log.get("user_id"),
                action=log["action"],
                entity_type=log.get("entity_type"),
                entity_id=log.get("entity_id"),
                old_values=log.get("old_values"),
                new_values=log.get("new_values"),
                ip_address=log.get("ip_address"),
                created_at=log.get("created_at"),
                user_username=log.get("user_username"),
            )
            for log in logs
        ]
        return AuditLogListResponse(items=items, total=len(items))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve audit logs: {str(e)}",
        )
