"""
schemas/preferences.py — Pydantic v2 schemas for user preferences.

Defines:
  - RiskTolerance  enum
  - TimeHorizon    enum
  - PreferencesUpdate   (partial update body — all fields optional)
  - PreferencesResponse (what the client receives)

Validation enforced here keeps routes and CRUD clean.
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Strict Enums
# ---------------------------------------------------------------------------
class RiskTolerance(str, Enum):
    """Defines how much market risk the user is comfortable with."""
    conservative = "conservative"
    moderate     = "moderate"
    aggressive   = "aggressive"


class TimeHorizon(str, Enum):
    """Defines the user's intended investment time frame."""
    short_term  = "short_term"
    medium_term = "medium_term"
    long_term   = "long_term"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_MAX_LIST_ITEMS = 20

def _validate_string_list(items: list[str], field_name: str) -> list[str]:
    """
    Common validation for preferred_kpis, preferred_sectors, preferred_geographies:
      - Lowercase normalize
      - Strip whitespace
      - Reject empty strings
      - Reject duplicates
      - Limit to _MAX_LIST_ITEMS items
    """
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in items:
        item = raw.strip().lower()
        if not item:
            raise ValueError(f"{field_name} must not contain empty strings")
        if not re.match(r"^[a-z0-9_ &\-/]+$", item):
            raise ValueError(
                f"{field_name} item '{item}' contains invalid characters"
            )
        if item in seen:
            raise ValueError(f"{field_name} contains duplicate: '{item}'")
        seen.add(item)
        cleaned.append(item)

    if len(cleaned) > _MAX_LIST_ITEMS:
        raise ValueError(
            f"{field_name} may contain at most {_MAX_LIST_ITEMS} items, got {len(cleaned)}"
        )
    return cleaned


# ---------------------------------------------------------------------------
# PreferencesUpdate — all fields optional for partial PATCH-style updates
# ---------------------------------------------------------------------------
class PreferencesUpdate(BaseModel):
    """
    Request body for PUT /preferences/me.

    Every field is optional — only provided fields will be updated.
    """

    risk_tolerance: Optional[RiskTolerance] = Field(
        default=None,
        description="Risk appetite: conservative | moderate | aggressive",
    )

    time_horizon: Optional[TimeHorizon] = Field(
        default=None,
        description="Investment horizon: short_term | medium_term | long_term",
    )

    preferred_kpis: Optional[list[str]] = Field(
        default=None,
        description="KPIs to prioritise, e.g. ['roe', 'ebitda', 'fcf']",
        max_length=_MAX_LIST_ITEMS,
    )

    preferred_sectors: Optional[list[str]] = Field(
        default=None,
        description="Sectors of interest, e.g. ['technology', 'healthcare']",
        max_length=_MAX_LIST_ITEMS,
    )

    preferred_geographies: Optional[list[str]] = Field(
        default=None,
        description="Geographies of interest, e.g. ['us', 'india', 'eu']",
        max_length=_MAX_LIST_ITEMS,
    )

    # ── Validators ────────────────────────────────────────────────────────────
    @field_validator("preferred_kpis")
    @classmethod
    def validate_kpis(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is None:
            return v
        return _validate_string_list(v, "preferred_kpis")

    @field_validator("preferred_sectors")
    @classmethod
    def validate_sectors(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is None:
            return v
        return _validate_string_list(v, "preferred_sectors")

    @field_validator("preferred_geographies")
    @classmethod
    def validate_geographies(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is None:
            return v
        return _validate_string_list(v, "preferred_geographies")


# ---------------------------------------------------------------------------
# PreferencesResponse — what the API returns
# ---------------------------------------------------------------------------
class PreferencesResponse(BaseModel):
    """
    Safe public representation of UserPreferences.
    """

    risk_tolerance:       RiskTolerance
    time_horizon:         TimeHorizon
    preferred_kpis:       list[str]
    preferred_sectors:    list[str]
    preferred_geographies: list[str]
    updated_at:           datetime

    model_config = {"from_attributes": True}
