"""
memory/models.py — SQLAlchemy ORM models: User and UserPreferences.

Phase 2 additions:
  - UserPreferences model (1-to-1 with User, linked via ForeignKey)
  - User.preferences relationship (back-populated from UserPreferences)
  - JSON columns for list fields (SQLite-compatible via sqlalchemy JSON type)

Design:
  - UUID primary key on both models
  - UserPreferences.user_id is UNIQUE (enforces 1-to-1)
  - Defaults match the spec (moderate, medium_term, two starter KPIs)
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------
class User(Base):
    """
    Authenticated user of the financial research agent.

    Fields:
        id             — UUID PK (auto-generated)
        unique_user_id — User-chosen login identifier (unique, indexed)
        full_name      — Display name
        dob_hash       — bcrypt hash of date_of_birth (login credential)
        created_at     — UTC timestamp of registration

    Relationships:
        preferences    — back-populated OneToOne to UserPreferences
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="UUID primary key — auto-generated on insert",
    )

    unique_user_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="User-chosen unique login handle (stored lowercase)",
    )

    full_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="User's display name",
    )

    dob_hash: Mapped[str] = mapped_column(
        String(72),
        nullable=False,
        comment="bcrypt hash of date_of_birth — raw DOB is never stored",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="UTC timestamp of account creation",
    )

    # ── Relationship: one user has exactly one preferences record ────────────
    preferences: Mapped["UserPreferences"] = relationship(
        "UserPreferences",
        back_populates="user",
        uselist=False,      # 1-to-1: uselist=False returns a single object, not a list
        cascade="all, delete-orphan",   # deleting User cascades to preferences
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} unique_user_id={self.unique_user_id!r}>"


# ---------------------------------------------------------------------------
# UserPreferences
# ---------------------------------------------------------------------------
class UserPreferences(Base):
    """
    Persistent personalisation profile for a single User.

    One-to-one with User (user_id is UNIQUE).
    JSON columns store lists — SQLAlchemy's JSON type works with both
    SQLite (as a text column serialised as JSON) and PostgreSQL (native JSONB
    with a minor URL change — production-ready as-is).

    Defaults:
        risk_tolerance       = "moderate"
        time_horizon         = "medium_term"
        preferred_kpis       = ["revenue_growth", "roe"]
        preferred_sectors    = []
        preferred_geographies = []
    """

    __tablename__ = "user_preferences"

    # ── Primary key ──────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="UUID primary key",
    )

    # ── Foreign key linking to User ──────────────────────────────────────────
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,        # UNIQUE enforces the 1-to-1 constraint at DB level
        nullable=False,
        index=True,
        comment="FK to users.id — unique for 1-to-1 relationship",
    )

    # ── Preference fields ────────────────────────────────────────────────────
    risk_tolerance: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="moderate",
        comment="RiskTolerance enum value: conservative | moderate | aggressive",
    )

    time_horizon: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="medium_term",
        comment="TimeHorizon enum value: short_term | medium_term | long_term",
    )

    # JSON columns — SQLite stores as TEXT, PostgreSQL as JSONB
    preferred_kpis: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: ["revenue_growth", "roe"],
        comment="List of KPI strings the user wants to track",
    )

    preferred_sectors: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,   # empty list factory
        comment="List of preferred sector strings",
    )

    preferred_geographies: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="List of preferred geography/market strings",
    )

    # ── Timestamp ────────────────────────────────────────────────────────────
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="UTC timestamp of last preferences update",
    )

    # ── Back-reference to User ───────────────────────────────────────────────
    user: Mapped["User"] = relationship(
        "User",
        back_populates="preferences",
    )

    def __repr__(self) -> str:
        return (
            f"<UserPreferences user_id={self.user_id} "
            f"risk={self.risk_tolerance} horizon={self.time_horizon}>"
        )
