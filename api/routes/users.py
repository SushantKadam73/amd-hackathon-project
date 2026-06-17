"""GRC Platform - Users API Routes.

Endpoints for listing and retrieving users. Users are used for
review workflow identity and audit trail purposes.
"""

from fastapi import APIRouter, HTTPException

from api.database import get_user, get_user_by_username
from api.models import UserResponse

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get(
    "",
    response_model=dict,
    summary="List all users",
)
async def list_users() -> dict:
    """Retrieve all registered users.

    Returns a list of users for identity selection in the UI.
    """
    try:
        from api.database import list_users as db_list_users
        users = db_list_users()
        return {"items": users, "total": len(users)}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve users: {str(e)}",
        )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    responses={
        200: {"description": "User details"},
        404: {"description": "User not found"},
    },
    summary="Get user by ID",
)
async def get_user_by_id(user_id: str) -> UserResponse:
    """Retrieve a single user by UUID."""
    try:
        user = get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User with id '{user_id}' not found",
            )
        return UserResponse(
            id=user["id"],
            username=user["username"],
            email=user.get("email"),
            full_name=user.get("full_name"),
            role=user.get("role"),
            is_active=user.get("is_active", True),
            created_at=user.get("created_at"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve user: {str(e)}",
        )
