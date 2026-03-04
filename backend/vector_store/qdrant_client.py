"""
vector_store/qdrant_client.py — Qdrant vector store client wrapper.

Phase 12: Full collection bootstrap, upsert, and similarity search enabled.

The QdrantClientWrapper is instantiated once in main.py lifespan
and stored as a module-level singleton so memory_service can access it.
"""

import logging
from typing import Optional

from qdrant_client import AsyncQdrantClient  # type: ignore

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class QdrantClientWrapper:
    """
    Thin async wrapper around the official qdrant-client.

    Phase 12 adds:
      - Collection bootstrap on connect (ensure_collection_exists)
    """

    def __init__(self) -> None:
        self._client: Optional[AsyncQdrantClient] = None
        self._healthy: bool = False

    async def connect(self) -> None:
        """
        Initialise the async Qdrant client and bootstrap the collection.
        Called once during FastAPI lifespan startup.
        Never raises — connectivity failure is logged and the server continues.
        """
        try:
            logger.info("Connecting to Qdrant", extra={"url": settings.QDRANT_URL})
            self._client = AsyncQdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
                timeout=10,
            )
            self._healthy = await self.health_check()
            if self._healthy:
                logger.info("Qdrant connected and healthy ✓")
                # Phase 12 — Bootstrap collection idempotently
                try:
                    from vector_store.collections import ensure_collection_exists
                    await ensure_collection_exists(self._client)
                except Exception as e:
                    logger.warning(f"Collection bootstrap failed (non-fatal): {e}")
            else:
                logger.warning(
                    "Qdrant client initialised but cluster unreachable — "
                    "vector memory will be unavailable"
                )
        except Exception as exc:
            self._client = None
            self._healthy = False
            logger.warning(
                "Qdrant connect() failed — running without vector memory",
                extra={"error": str(exc)},
            )

    async def disconnect(self) -> None:
        """Close the Qdrant client — called on application shutdown."""
        if self._client is not None:
            await self._client.close()
            self._client = None
            self._healthy = False
        logger.info("Qdrant client disconnected")

    async def health_check(self) -> bool:
        """Ping the Qdrant cluster to verify connectivity."""
        if self._client is None:
            return False
        try:
            await self._client.get_collections()
            logger.debug("Qdrant health check passed")
            return True
        except Exception as exc:
            logger.warning("Qdrant health check failed", extra={"error": str(exc)})
            return False

    @property
    def is_healthy(self) -> bool:
        """Return last known health status."""
        return self._healthy

    @property
    def client(self) -> Optional[AsyncQdrantClient]:
        """Direct access to the underlying client for advanced usage."""
        return self._client


# ---------------------------------------------------------------------------
# Module-level singleton — shared across the entire application
# Initialised by calling await qdrant_wrapper.connect() in main.py lifespan
# ---------------------------------------------------------------------------
qdrant_wrapper = QdrantClientWrapper()
