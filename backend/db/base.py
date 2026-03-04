"""
db/base.py — Declarative base for all SQLAlchemy ORM models.

Import `Base` into every model file and use it as the parent class:
    from db.base import Base
    class MyModel(Base): ...

This module intentionally contains NO model definitions.
Models are added in later phases (Phase 1+).
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Shared base class for all ORM models.
    Using SQLAlchemy 2.0 DeclarativeBase style for full type-checking support.
    """
    pass
