"""GRC Platform - Framework API Routes.

Endpoints for managing compliance frameworks and viewing controls.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request

from api.database import (
    create_framework,
    get_framework,
    list_controls_by_framework,
    list_frameworks,
)
from api.models import (
    ControlListResponse,
    ControlResponse,
    ErrorResponse,
    FrameworkCreate,
    FrameworkListResponse,
    FrameworkResponse,
)

router = APIRouter(prefix="/api/v1/frameworks", tags=["Frameworks"])


@router.get(
    "",
    response_model=FrameworkListResponse,
    responses={200: {"description": "List of all frameworks"}},
    summary="List all compliance frameworks",
)
async def get_frameworks() -> FrameworkListResponse:
    """Retrieve all compliance frameworks.

    Returns a list of all active frameworks (e.g., NIST SP 800-53).
    """
    try:
        frameworks = list_frameworks()
        items = [
            FrameworkResponse(
                id=fw["id"],
                name=fw["name"],
                version=fw.get("version"),
                description=fw.get("description"),
                created_at=fw.get("created_at"),
            )
            for fw in frameworks
        ]
        return FrameworkListResponse(items=items, total=len(items))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve frameworks: {str(e)}",
        )


@router.get(
    "/{framework_id}",
    response_model=FrameworkResponse,
    responses={
        200: {"description": "Framework details"},
        404: {"description": "Framework not found", "model": ErrorResponse},
    },
    summary="Get a framework by ID",
)
async def get_framework_by_id(framework_id: str) -> FrameworkResponse:
    """Retrieve a single compliance framework by its UUID."""
    try:
        fw = get_framework(framework_id)
        if not fw:
            raise HTTPException(
                status_code=404,
                detail=f"Framework with id '{framework_id}' not found",
            )
        return FrameworkResponse(
            id=fw["id"],
            name=fw["name"],
            version=fw.get("version"),
            description=fw.get("description"),
            created_at=fw.get("created_at"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve framework: {str(e)}",
        )


@router.post(
    "",
    response_model=FrameworkResponse,
    status_code=201,
    responses={
        201: {"description": "Framework created"},
        422: {"description": "Validation error", "model": ErrorResponse},
    },
    summary="Create a new framework",
)
async def create_new_framework(
    body: FrameworkCreate,
    request: Request,
) -> FrameworkResponse:
    """Create a new compliance framework.

    Accepts a JSON body with name, optional version, and optional description.
    Creates an audit log entry for the mutation.
    """
    try:
        client_ip = request.client.host if request.client else None
        fw = create_framework(
            name=body.name,
            version=body.version,
            description=body.description,
            ip_address=client_ip,
        )
        return FrameworkResponse(
            id=fw["id"],
            name=fw["name"],
            version=fw.get("version"),
            description=fw.get("description"),
            created_at=fw.get("created_at"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create framework: {str(e)}",
        )


@router.get(
    "/{framework_id}/controls",
    response_model=ControlListResponse,
    responses={
        200: {"description": "List of controls for the framework"},
        404: {"description": "Framework not found", "model": ErrorResponse},
    },
    summary="List controls for a framework",
)
async def get_controls_for_framework(
    framework_id: str,
) -> ControlListResponse:
    """Retrieve all controls belonging to a specific framework.

    Returns control details including artifact requirements and
    cross-framework mappings.
    """
    try:
        # Verify framework exists
        fw = get_framework(framework_id)
        if not fw:
            raise HTTPException(
                status_code=404,
                detail=f"Framework with id '{framework_id}' not found",
            )

        controls = list_controls_by_framework(framework_id)
        items = [
            ControlResponse(
                id=ctrl["id"],
                framework_id=ctrl["framework_id"],
                control_id=ctrl["control_id"],
                title=ctrl["title"],
                description=ctrl.get("description"),
                control_family=ctrl.get("control_family"),
                priority=ctrl.get("priority", "medium"),
                artifact_requirements=ctrl.get("artifact_requirements"),
                cross_framework_mappings=ctrl.get("cross_framework_mappings"),
            )
            for ctrl in controls
        ]
        return ControlListResponse(items=items, total=len(items))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve controls: {str(e)}",
        )
