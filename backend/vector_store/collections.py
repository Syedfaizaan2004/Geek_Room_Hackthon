"""
vector_store/collections.py - Qdrant collection bootstrap (Phase 12).

Ensures collection exists and required payload indexes are present.
"""

import logging

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, PayloadSchemaType, VectorParams

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

COLLECTION_NAME: str = settings.QDRANT_COLLECTION
VECTOR_DIM: int = 384
DISTANCE_METRIC = Distance.COSINE


async def ensure_collection_exists(client: AsyncQdrantClient) -> bool:
    """
    Idempotent collection bootstrap.
    Creates collection and ensures payload indexes required by filters.
    """
    try:
        existing = await client.get_collections()
        existing_names = [c.name for c in existing.collections]

        if COLLECTION_NAME in existing_names:
            logger.info("Qdrant collection '%s' already exists", COLLECTION_NAME)
        else:
            logger.info(
                "Creating Qdrant collection '%s' (dim=%s, metric=cosine)",
                COLLECTION_NAME,
                VECTOR_DIM,
            )
            await client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_DIM, distance=DISTANCE_METRIC),
            )
            logger.info("Qdrant collection '%s' created", COLLECTION_NAME)

        # Required for filtered memory queries on newer Qdrant versions.
        index_specs = [
            ("user_id", PayloadSchemaType.KEYWORD),
            ("ticker", PayloadSchemaType.KEYWORD),
            ("sector", PayloadSchemaType.KEYWORD),
            ("insight_type", PayloadSchemaType.KEYWORD),
            ("risk_score", PayloadSchemaType.FLOAT),
            ("financial_health_score", PayloadSchemaType.FLOAT),
            ("timestamp", PayloadSchemaType.DATETIME),
        ]
        for field_name, field_schema in index_specs:
            try:
                await client.create_payload_index(
                    collection_name=COLLECTION_NAME,
                    field_name=field_name,
                    field_schema=field_schema,
                )
            except Exception as exc:
                logger.debug("Skipping payload index ensure for %s: %s", field_name, exc)

        return True

    except Exception as exc:
        logger.error("Failed to ensure Qdrant collection: %s", exc)
        return False
