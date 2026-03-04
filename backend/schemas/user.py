"""
schemas/user.py — Pydantic v2 schemas for user create/response.

No ORM objects ever cross the HTTP boundary — only these schemas do.
"""

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class UserCreate(BaseModel):
    """
    Payload for POST /auth/register.

    Validation rules enforced here — routes stay logic-free.
    """

    full_name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="User's full name",
        examples=["Alice Johnson"],
    )

    date_of_birth: str = Field(
        ...,
        description="Date of birth in YYYY-MM-DD format",
        examples=["1995-07-24"],
    )

    unique_user_id: str = Field(
        ...,
        min_length=5,
        max_length=50,
        description="Globally unique identifier chosen by the user",
        examples=["alice_fin_007"],
    )

    # ── Validators ────────────────────────────────────────────────────────────
    @field_validator("date_of_birth")
    @classmethod
    def validate_dob_format(cls, v: str) -> str:
        """Enforce YYYY-MM-DD and reject obviously invalid dates."""
        pattern = r"^\d{4}-\d{2}-\d{2}$"
        if not re.match(pattern, v):
            raise ValueError("date_of_birth must be in YYYY-MM-DD format")

        # Further validate it parses as a real date
        try:
            from datetime import date
            parsed = date.fromisoformat(v)
            if parsed.year < 1900 or parsed > date.today():
                raise ValueError("date_of_birth must be a past date after 1900")
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid date_of_birth: {exc}") from exc

        return v

    @field_validator("unique_user_id")
    @classmethod
    def validate_user_id_chars(cls, v: str) -> str:
        """Allow only alphanumerics, underscores, hyphens."""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "unique_user_id may only contain letters, digits, underscores, or hyphens"
            )
        return v.strip().lower()

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        return v.strip()


class UserResponse(BaseModel):
    """
    Safe public representation of a User — never exposes dob_hash or id internals.
    Returned from /register and /me routes.
    """

    id: UUID
    full_name: str
    unique_user_id: str
    created_at: datetime

    model_config = {"from_attributes": True}  # Allow building from ORM model
