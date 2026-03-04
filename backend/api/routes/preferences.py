"""
api/routes/preferences.py — User preferences endpoints.

Endpoints:
  GET /preferences/me   — fetch the authenticated user's preferences
  PUT /preferences/me   — partial update of authenticated user's preferences

Architecture:
  - get_current_user dependency provides the authenticated User
  - No user_id accepted from client — always derived from the JWT token
  - No business logic here — all logic delegated to memory/crud.py
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.routes.auth import get_current_user
from db.session import get_db
from memory import crud
from memory.models import User
from schemas.preferences import PreferencesResponse, PreferencesUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/preferences", tags=["Preferences"])


# ---------------------------------------------------------------------------
# GET /preferences/me
# ---------------------------------------------------------------------------
@router.get(
    "/me",
    response_model=PreferencesResponse,
    summary="Get current user's preferences",
    responses={
        401: {"description": "Missing or invalid token"},
        404: {"description": "Preferences not found"},
    },
)
async def get_my_preferences(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> PreferencesResponse:
    """
    Returns the personalisation preferences for the currently authenticated user.

    Requires: `Authorization: Bearer <token>`
    """
    prefs = await crud.get_preferences_by_user_id(db, current_user.id)

    if prefs is None:
        # Should never happen for users created via register, but guard defensively
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": "Preferences not found",
                "detail": "No preferences record exists for this user. This should not happen. Please contact support.",
            },
        )

    return PreferencesResponse.model_validate(prefs)


# ---------------------------------------------------------------------------
# PUT /preferences/me
# ---------------------------------------------------------------------------
@router.put(
    "/me",
    response_model=PreferencesResponse,
    summary="Update current user's preferences (partial update allowed)",
    responses={
        401: {"description": "Missing or invalid token"},
        422: {"description": "Validation error — invalid enum or list"},
    },
)
async def update_my_preferences(
    payload: PreferencesUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> PreferencesResponse:
    """
    Partially update preferences for the currently authenticated user.

    All fields are optional — only the fields you provide will be updated.

    - `risk_tolerance`:        `conservative` | `moderate` | `aggressive`
    - `time_horizon`:          `short_term` | `medium_term` | `long_term`
    - `preferred_kpis`:        list of lowercase strings, max 20, no duplicates
    - `preferred_sectors`:     list of lowercase strings, max 20, no duplicates
    - `preferred_geographies`: list of lowercase strings, max 20, no duplicates

    Requires: `Authorization: Bearer <token>`
    """
    try:
        updated = await crud.update_preferences(db, current_user.id, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "success": False,
                "error": "Preferences update failed",
                "detail": str(exc),
            },
        ) from exc

    return PreferencesResponse.model_validate(updated)
