"""
vector_store/memory_service.py — Qdrant Memory Service (Phase 12).

Provides high-level async operations:
  - store_insight_embedding()    → upsert a research session into Qdrant
  - retrieve_similar_insights()  → semantic search filtered by user_id
  - find_similar_companies()     → cross-user similarity by ticker embedding
  - search_by_risk_pattern()     → metadata-filtered risk threshold query

All methods are non-fatal — Qdrant unavailability never crashes a request.
"""

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    Range,
)

from vector_store.collections import COLLECTION_NAME
from vector_store.embeddings import generate_embedding, build_insight_text
from schemas.memory import MemorySimilarResult, RiskPatternResult, MemoryRecentResult

logger = logging.getLogger(__name__)


def _record_qdrant_latency(start_ts: float) -> None:
    from utils.performance_logger import perf_logger
    perf_logger.record_qdrant((time.perf_counter() - start_ts) * 1000)


# ── Store ─────────────────────────────────────────────────────────────────────

async def store_insight_embedding(
    client: AsyncQdrantClient,
    user_id: str,
    ticker: str,
    insight_data: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Generate an embedding from structured insight data and upsert into Qdrant.

    Args:
        client:       AsyncQdrantClient instance
        user_id:      The authenticated user's ID
        ticker:       Stock symbol (e.g. "AAPL")
        insight_data: Dict from InsightResponse.model_dump()
        metadata:     Optional extra fields (risk_score, health_score, sector)

    Returns:
        True on success, False on failure.
    """
    try:
        # Build embeddable text blob from structured insight fields
        text = build_insight_text(
            ticker=ticker,
            executive_summary=insight_data.get("executive_summary", ""),
            strengths=insight_data.get("strengths", []),
            risks=insight_data.get("risks", []),
            bull_thesis=insight_data.get("bull_thesis", []),
            bear_thesis=insight_data.get("bear_thesis", []),
            plain_language_summary=insight_data.get("plain_language_summary", ""),
        )

        vector = generate_embedding(text)
        if vector is None:
            logger.warning(f"Embedding generation failed for {ticker} — not stored")
            return False

        meta = metadata or {}
        point_id = str(uuid.uuid4())

        payload = {
            "user_id": user_id,
            "ticker": ticker.upper(),
            "risk_score": float(meta.get("risk_score", 0.0)),
            "financial_health_score": float(meta.get("financial_health_score", 0.0)),
            "sector": meta.get("sector", "unknown"),
            "insight_type": meta.get("insight_type", "deep"),
            "summary_excerpt": text[:400],   # First 400 chars as preview
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        q_start = time.perf_counter()
        await client.upsert(
            collection_name=COLLECTION_NAME,
            points=[PointStruct(id=point_id, vector=vector, payload=payload)],
        )
        _record_qdrant_latency(q_start)
        logger.info(f"Stored insight embedding for {ticker} (user={user_id}, id={point_id})")
        return True

    except Exception as e:
        logger.error(f"Failed to store insight embedding for {ticker}: {e}")
        return False


# ── Retrieve — user-scoped semantic search ────────────────────────────────────

async def retrieve_similar_insights(
    client: AsyncQdrantClient,
    query_text: str,
    user_id: str,
    top_k: int = 5,
) -> List[MemorySimilarResult]:
    """
    Search Qdrant for insights semantically similar to query_text,
    scoped to the given user_id.

    Returns ranked list of MemorySimilarResult.
    """
    try:
        vector = generate_embedding(query_text)
        if vector is None:
            return []

        q_start = time.perf_counter()
        response = await client.query_points(
            collection_name=COLLECTION_NAME,
            query=vector,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=user_id),
                    )
                ]
            ),
            limit=top_k,
            with_payload=True,
        )
        _record_qdrant_latency(q_start)

        results = response.points if hasattr(response, "points") else []
        output = []
        for hit in results:
            p = hit.payload or {}
            output.append(MemorySimilarResult(
                ticker=p.get("ticker", "?"),
                similarity_score=round(float(hit.score), 4),
                summary_excerpt=p.get("summary_excerpt", ""),
                risk_score=p.get("risk_score", 0.0),
                financial_health_score=p.get("financial_health_score", 0.0),
                insight_type=p.get("insight_type", "deep"),
                stored_at=_parse_ts(p.get("timestamp")),
            ))
        return output

    except Exception as e:
        logger.error(f"retrieve_similar_insights failed: {e}")
        return []


# ── Similar company discovery — cross-user vector search ─────────────────────

async def find_similar_companies(
    client: AsyncQdrantClient,
    ticker: str,
    insight_text: str,
    top_k: int = 5,
) -> List[MemorySimilarResult]:
    """
    Find tickers that are semantically similar to the given ticker's insight text.
    Not scoped by user_id — searches across all stored insights.

    Excludes the query ticker itself from results.
    """
    try:
        vector = generate_embedding(insight_text)
        if vector is None:
            return []

        q_start = time.perf_counter()
        response = await client.query_points(
            collection_name=COLLECTION_NAME,
            query=vector,
            limit=top_k + 3,   # Fetch extra to compensate for self-exclusion
            with_payload=True,
        )
        _record_qdrant_latency(q_start)

        results = response.points if hasattr(response, "points") else []
        seen_tickers: set = set()
        output = []
        for hit in results:
            p = hit.payload or {}
            t = p.get("ticker", "?")

            if t.upper() == ticker.upper():
                continue   # exclude self
            if t in seen_tickers:
                continue   # deduplicate by ticker
            seen_tickers.add(t)

            output.append(MemorySimilarResult(
                ticker=t,
                similarity_score=round(float(hit.score), 4),
                summary_excerpt=p.get("summary_excerpt", ""),
                risk_score=p.get("risk_score", 0.0),
                financial_health_score=p.get("financial_health_score", 0.0),
                insight_type=p.get("insight_type", "deep"),
                stored_at=_parse_ts(p.get("timestamp")),
            ))
            if len(output) >= top_k:
                break

        return output

    except Exception as e:
        logger.error(f"find_similar_companies failed for {ticker}: {e}")
        return []


# ── Risk pattern search — metadata filter ─────────────────────────────────────

async def search_by_risk_pattern(
    client: AsyncQdrantClient,
    risk_threshold: float,
    limit: int = 20,
) -> List[RiskPatternResult]:
    """
    Return tickers in memory whose composite risk score exceeds the threshold.
    Uses Qdrant metadata filtering (no embedding necessary).
    """
    try:
        q_start = time.perf_counter()
        results = await client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="risk_score",
                        range=Range(gte=risk_threshold),
                    )
                ]
            ),
            limit=limit,
            with_payload=True,
        )
        _record_qdrant_latency(q_start)

        points = results[0]  # scroll returns (points, next_offset)
        output = []
        seen: set = set()
        for point in points:
            p = point.payload or {}
            t = p.get("ticker", "?")
            if t in seen:
                continue
            seen.add(t)
            output.append(RiskPatternResult(
                ticker=t,
                risk_score=p.get("risk_score", 0.0),
                insight_type=p.get("insight_type", "deep"),
                stored_at=_parse_ts(p.get("timestamp")),
            ))

        # Sort by risk descending
        output.sort(key=lambda x: x.risk_score, reverse=True)
        return output

    except Exception as e:
        logger.error(f"search_by_risk_pattern failed (threshold={risk_threshold}): {e}")
        return []


# —— Recent stored analyses ————————————————————————————————————————————————————————————————

async def retrieve_recent_insights(
    client: AsyncQdrantClient,
    user_id: str,
    limit: int = 20,
) -> List[MemoryRecentResult]:
    """
    Return recent stored insights for a specific user.
    """
    try:
        fetch_limit = min(max(limit * 5, 40), 250)
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=user_id),
                )
            ]
        )

        q_start = time.perf_counter()
        try:
            points, _ = await client.scroll(
                collection_name=COLLECTION_NAME,
                scroll_filter=query_filter,
                limit=fetch_limit,
                with_payload=True,
                order_by="timestamp",
            )
        except Exception:
            # Fallback for clusters where payload ordering is unsupported.
            points, _ = await client.scroll(
                collection_name=COLLECTION_NAME,
                scroll_filter=query_filter,
                limit=fetch_limit,
                with_payload=True,
            )
        _record_qdrant_latency(q_start)

        output: List[MemoryRecentResult] = []
        for point in points:
            payload = point.payload or {}
            output.append(MemoryRecentResult(
                ticker=payload.get("ticker", "?"),
                summary_excerpt=payload.get("summary_excerpt", ""),
                risk_score=payload.get("risk_score", 0.0),
                financial_health_score=payload.get("financial_health_score", 0.0),
                insight_type=payload.get("insight_type", "deep"),
                stored_at=_parse_ts(payload.get("timestamp")),
            ))

        output.sort(
            key=lambda item: item.stored_at or datetime(1970, 1, 1, tzinfo=timezone.utc),
            reverse=True,
        )
        return output[:limit]

    except Exception as e:
        logger.error(f"retrieve_recent_insights failed for user={user_id}: {e}")
        return []


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_ts(ts_str: Optional[str]) -> Optional[datetime]:
    if not ts_str:
        return None
    try:
        return datetime.fromisoformat(ts_str)
    except Exception:
        return None
