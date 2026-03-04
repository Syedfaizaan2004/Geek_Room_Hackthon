"""
memory/crud.py — Async CRUD for User and UserPreferences.

Rules:
  - No HTTP logic (no Request / Response objects)
  - No route-level concerns
  - All DB operations async
  - Raise domain-specific exceptions — routes map them to HTTP codes

User functions:
  - get_user_by_unique_id()
  - create_user()              ← now also creates default UserPreferences
  - authenticate_user()

Preferences functions (Phase 2):
  - create_default_preferences()
  - get_preferences_by_user_id()
  - update_preferences()
"""

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from memory.models import User, UserPreferences
from schemas.preferences import PreferencesUpdate
from schemas.user import UserCreate
from utils.security import hash_dob, verify_dob

logger = logging.getLogger(__name__)


# ===========================================================================
# User CRUD
# ===========================================================================

async def get_user_by_unique_id(
    db: AsyncSession,
    unique_user_id: str,
) -> Optional[User]:
    """Fetch a User by their unique_user_id. Returns None if not found."""
    started = time.perf_counter()
    result = await db.execute(
        select(User).where(User.unique_user_id == unique_user_id.lower())
    )
    from utils.performance_logger import perf_logger
    perf_logger.record_db((time.perf_counter() - started) * 1000)
    return result.scalars().first()


async def create_user(
    db: AsyncSession,
    user_data: UserCreate,
) -> User:
    """
    Create a new User and automatically create their default UserPreferences
    within the same database transaction.

    Steps:
      1. Check unique_user_id is not taken  → raise ValueError on duplicate
      2. Create User row
      3. flush() to assign PK
      4. Create UserPreferences row linked to the new user
      5. flush() + refresh both objects
      (caller's session commits the full transaction)

    Args:
        db:        Active async database session.
        user_data: Validated UserCreate schema.

    Returns:
        Newly created User with preferences relationship populated.

    Raises:
        ValueError: If unique_user_id is already registered.
    """
    # 1. Duplicate check
    existing = await get_user_by_unique_id(db, user_data.unique_user_id)
    if existing is not None:
        raise ValueError(
            f"unique_user_id '{user_data.unique_user_id}' is already registered"
        )

    # 2. Create User
    dob_hash = hash_dob(user_data.date_of_birth)
    new_user = User(
        unique_user_id=user_data.unique_user_id.lower(),
        full_name=user_data.full_name.strip(),
        dob_hash=dob_hash,
    )
    db.add(new_user)
    await db.flush()             # assign new_user.id
    await db.refresh(new_user)

    # 3. Auto-create default preferences — same transaction, no separate commit
    await create_default_preferences(db, new_user.id)

    logger.info(
        "User + preferences created",
        extra={"unique_user_id": new_user.unique_user_id, "id": str(new_user.id)},
    )
    return new_user


async def authenticate_user(
    db: AsyncSession,
    unique_user_id: str,
    raw_dob: str,
) -> Optional[User]:
    """
    Verify login credentials. Returns User on success, None on failure.
    Same error for "not found" and "wrong DOB" — prevents user enumeration.
    """
    user = await get_user_by_unique_id(db, unique_user_id)
    if user is None:
        verify_dob(raw_dob, "$2b$12$dummyhashfortimingattackprevention12345678901")
        logger.debug("Login failed — user not found", extra={"unique_user_id": unique_user_id})
        return None

    if not verify_dob(raw_dob, user.dob_hash):
        logger.warning("Login failed — invalid DOB", extra={"unique_user_id": unique_user_id})
        return None

    logger.info("Login success", extra={"unique_user_id": unique_user_id})
    return user


# ===========================================================================
# Preferences CRUD  (Phase 2)
# ===========================================================================

async def create_default_preferences(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> UserPreferences:
    """
    Create a UserPreferences row with safe default values for a new user.

    This is called inside create_user() — it shares the same transaction.
    Do NOT call this independently unless you have checked the user exists.

    Defaults:
        risk_tolerance       = "moderate"
        time_horizon         = "medium_term"
        preferred_kpis       = ["revenue_growth", "roe"]
        preferred_sectors    = []
        preferred_geographies = []
    """
    prefs = UserPreferences(
        user_id=user_id,
        risk_tolerance="moderate",
        time_horizon="medium_term",
        preferred_kpis=["revenue_growth", "roe"],
        preferred_sectors=[],
        preferred_geographies=[],
    )
    db.add(prefs)
    await db.flush()
    await db.refresh(prefs)

    logger.debug(
        "Default preferences created",
        extra={"user_id": str(user_id)},
    )
    return prefs


async def get_preferences_by_user_id(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> Optional[UserPreferences]:
    """
    Fetch a UserPreferences record by the owning user's UUID.

    Returns None if preferences do not exist yet (should not happen for
    users created via create_user, but guards against data inconsistency).
    """
    started = time.perf_counter()
    result = await db.execute(
        select(UserPreferences).where(UserPreferences.user_id == user_id)
    )
    from utils.performance_logger import perf_logger
    perf_logger.record_db((time.perf_counter() - started) * 1000)
    return result.scalars().first()


async def update_preferences(
    db: AsyncSession,
    user_id: uuid.UUID,
    updates: PreferencesUpdate,
) -> UserPreferences:
    """
    Partially update a UserPreferences record.

    Only fields that are explicitly provided (not None) are updated.
    This implements PATCH semantics even though the HTTP verb is PUT,
    as required by the spec (partial update allowed).

    Args:
        db:       Active async database session.
        user_id:  UUID of the owning user.
        updates:  Validated PreferencesUpdate schema (all fields optional).

    Returns:
        The updated UserPreferences ORM instance.

    Raises:
        ValueError: If preferences are not found for the given user_id.
    """
    prefs = await get_preferences_by_user_id(db, user_id)
    if prefs is None:
        # Defensive: auto-create if missing (e.g. legacy accounts)
        logger.warning(
            "Preferences not found — auto-creating defaults",
            extra={"user_id": str(user_id)},
        )
        prefs = await create_default_preferences(db, user_id)

    # Apply only the non-None fields from the update payload
    changed = False

    if updates.risk_tolerance is not None:
        prefs.risk_tolerance = updates.risk_tolerance.value
        changed = True

    if updates.time_horizon is not None:
        prefs.time_horizon = updates.time_horizon.value
        changed = True

    if updates.preferred_kpis is not None:
        prefs.preferred_kpis = updates.preferred_kpis
        changed = True

    if updates.preferred_sectors is not None:
        prefs.preferred_sectors = updates.preferred_sectors
        changed = True

    if updates.preferred_geographies is not None:
        prefs.preferred_geographies = updates.preferred_geographies
        changed = True

    if changed:
        prefs.updated_at = datetime.now(timezone.utc)
        db.add(prefs)
        await db.flush()
        await db.refresh(prefs)
        logger.info(
            "Preferences updated",
            extra={"user_id": str(user_id)},
        )
    else:
        logger.debug(
            "Preferences PUT received but nothing changed",
            extra={"user_id": str(user_id)},
        )

    return prefs
