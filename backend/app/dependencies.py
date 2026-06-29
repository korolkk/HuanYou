"""FastAPI dependency injection extensions."""

from app.models.base import get_db

__all__ = ["get_db"]
