"""
schemas/auth.py — Pydantic v2 schemas for login and token responses.
"""

import re
from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    """Payload for POST /auth/login."""

    unique_user_id: str = Field(
        ...,
        min_length=5,
        max_length=50,
        description="The user's unique identifier",
        examples=["alice_fin_007"],
    )

    date_of_birth: str = Field(
        ...,
        description="Date of birth in YYYY-MM-DD format (used as password)",
        examples=["1995-07-24"],
    )

    @field_validator("unique_user_id")
    @classmethod
    def normalise_user_id(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob_format(cls, v: str) -> str:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("date_of_birth must be in YYYY-MM-DD format")
        return v


class TokenResponse(BaseModel):
    """
    Response for POST /auth/login.

    access_token:  the raw JWT string — client stores and sends as
                   Authorization: Bearer <token>
    token_type:    always "bearer" per OAuth2 convention
    expires_in:    seconds until the token expires (from config)
    """

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Token validity in seconds")
