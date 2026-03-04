"""
vector_store/embeddings.py — Deterministic text embedding pipeline (Phase 12).

Uses sentence-transformers `all-MiniLM-L6-v2`:
  - 384-dimensional output
  - Fully deterministic (same input → same vector every time)
  - Lightweight (~80MB, runs on CPU)
  - No API calls, no network dependency after first download
  - Apache-2.0 licensed

The model is loaded once as a module-level singleton to avoid
repeated disk I/O on every embedding call.
"""

import logging
import hashlib
import math
import re
from typing import List, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 384
_MODEL_NAME = "all-MiniLM-L6-v2"
_FALLBACK_WARNED = False


@lru_cache(maxsize=1)
def _get_model():
    """
    Lazy-load the SentenceTransformer model.
    Called once; subsequent calls return the cached model instantly.
    """
    try:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading embedding model: {_MODEL_NAME}")
        model = SentenceTransformer(_MODEL_NAME)
        logger.info(f"Embedding model loaded ✓ (dim={EMBEDDING_DIM})")
        return model
    except ImportError:
        logger.error(
            "sentence-transformers not installed. "
            "Run: pip install sentence-transformers"
        )
        return None
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        return None


def generate_embedding(text: str) -> Optional[List[float]]:
    """
    Generate a deterministic 384-dimensional embedding for the given text.

    Args:
        text: The text to embed (executive summary, insights, etc.)

    Returns:
        List of 384 floats, or None if the model failed to load.
    """
    if not text or not text.strip():
        logger.warning("generate_embedding called with empty text")
        return None

    model = _get_model()
    if model is None:
        global _FALLBACK_WARNED
        if not _FALLBACK_WARNED:
            logger.warning(
                "Embedding model unavailable. Using deterministic hash embedding fallback."
            )
            _FALLBACK_WARNED = True
        return _hash_fallback_embedding(text)

    try:
        vector = model.encode(text, normalize_embeddings=True).tolist()
        return vector
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        return _hash_fallback_embedding(text)


def _hash_fallback_embedding(text: str) -> List[float]:
    """
    Deterministic local embedding fallback when sentence-transformers is unavailable.
    Uses hashed token projections into a fixed 384-dim vector and L2 normalizes output.
    """
    tokens = re.findall(r"[a-z0-9_]+", text.lower())
    if not tokens:
        tokens = [text.lower()]

    vec = [0.0] * EMBEDDING_DIM

    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        # Project each token into 4 signed buckets for better spread.
        for i in range(0, 8, 2):
            idx = int.from_bytes(digest[i:i + 2], "big") % EMBEDDING_DIM
            sign = -1.0 if (digest[(i + 8) % len(digest)] & 1) else 1.0
            weight = 0.5 + (digest[(i + 9) % len(digest)] / 255.0)
            vec[idx] += sign * weight

    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return vec
    return [v / norm for v in vec]


def build_insight_text(
    ticker: str,
    executive_summary: str = "",
    strengths: Optional[List[str]] = None,
    risks: Optional[List[str]] = None,
    bull_thesis: Optional[List[str]] = None,
    bear_thesis: Optional[List[str]] = None,
    plain_language_summary: str = "",
) -> str:
    """
    Concatenate structured insight fields into a single embeddable text blob.

    Order is intentional — summary first (highest weight in sentence-transformers),
    then pros/cons, then theses.
    """
    parts = [f"Ticker: {ticker}."]

    if executive_summary:
        parts.append(executive_summary)

    if plain_language_summary:
        parts.append(plain_language_summary)

    if strengths:
        parts.append("Strengths: " + " ".join(strengths))

    if risks:
        parts.append("Risks: " + " ".join(risks))

    if bull_thesis:
        parts.append("Bull case: " + " ".join(bull_thesis))

    if bear_thesis:
        parts.append("Bear case: " + " ".join(bear_thesis))

    return " ".join(parts)
