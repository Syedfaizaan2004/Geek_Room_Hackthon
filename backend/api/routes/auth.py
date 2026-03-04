"""
api/routes/auth.py — Authentication routes.

Endpoints:
  POST /auth/register   — register a new user
  POST /auth/login      — login, returns JWT
  GET  /auth/me         — return current authenticated user

Architecture: No business logic lives here.
All logic is delegated to memory/crud.py and utils/security.py.
Routes only handle HTTP concerns: request parsing, status codes, responses.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from memory import crud
from memory.models import User
from schemas.auth import LoginRequest, TokenResponse
from schemas.user import UserCreate, UserResponse
from utils.security import create_access_token, verify_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Bearer token extractor — FastAPI reads "Authorization: Bearer <token>"
_bearer_scheme = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Auth dependency — reusable across all protected routes
# ---------------------------------------------------------------------------
async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(_bearer_scheme),
    ],
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency that extracts, verifies a JWT, and returns the User.

    Usage:
        current_user: User = Depends(get_current_user)

    Raises:
        HTTP 401 if token is missing, expired, or invalid.
        HTTP 404 if the user encoded in the token no longer exists.
    """
    _unauth = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "success": False,
            "error": "Authentication required",
            "detail": "Provide a valid Bearer token in the Authorization header",
        },
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise _unauth

    try:
        payload = verify_token(credentials.credentials)
    except ValueError as exc:
        logger.debug("Token verification failed", extra={"error": str(exc)})
        raise _unauth from exc

    # The 'sub' claim holds the unique_user_id
    unique_user_id: str = payload.get("sub", "")
    if not unique_user_id:
        raise _unauth

    user = await crud.get_user_by_unique_id(db, unique_user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": "User not found",
                "detail": "The authenticated user no longer exists",
            },
        )

    return user


# ---------------------------------------------------------------------------
# POST /auth/register
# ---------------------------------------------------------------------------
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    responses={
        409: {"description": "unique_user_id already taken"},
        422: {"description": "Validation error"},
    },
)
async def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Register a new user account.

    - `full_name`       — minimum 3 characters
    - `unique_user_id`  — minimum 5 chars, alphanumeric + underscore/hyphen
    - `date_of_birth`   — YYYY-MM-DD format (used as login credential, never stored raw)

    Returns the created user profile (no sensitive data).
    """
    try:
        user = await crud.create_user(db, payload)
    except ValueError as exc:
        # Duplicate unique_user_id raised by CRUD layer
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "success": False,
                "error": "Registration failed",
                "detail": str(exc),
            },
        ) from exc

    return UserResponse.model_validate(user)


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------
@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive a JWT access token",
    responses={
        401: {"description": "Invalid credentials"},
        422: {"description": "Validation error"},
    },
)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate using `unique_user_id` + `date_of_birth`.

    On success returns a JWT access token.
    The same error is returned whether the user doesn't exist or the DOB is wrong
    (prevents user enumeration attacks).
    """
    user = await crud.authenticate_user(
        db,
        unique_user_id=payload.unique_user_id,
        raw_dob=payload.date_of_birth,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": "Authentication failed",
                "detail": "Invalid unique_user_id or date_of_birth",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Encode the unique_user_id as the JWT subject
    token, expires_in = create_access_token({"sub": user.unique_user_id})

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
    )


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------
@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user",
    responses={
        401: {"description": "Missing or invalid token"},
        404: {"description": "User not found"},
    },
)
async def me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    """
    Returns the profile of the currently authenticated user.

    Requires: `Authorization: Bearer <token>`
    """
    return UserResponse.model_validate(current_user)
