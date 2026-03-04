"""
utils/performance_logger.py — Phase 16 Performance Logger & Metrics Collector.

Tracks:
- Execution time per workflow mode
- Total request count
- LLM token usage and accumulated cost
- Qdrant query latency
- DB query duration

Exposes metrics via get_metrics_snapshot() for GET /metrics endpoint.
"""

import time
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Deque

logger = logging.getLogger(__name__)

# Rolling window size (last N samples for average calculation)
_WINDOW = 100


@dataclass
class _LatencySeries:
    """Holds a rolling deque of latency samples in ms."""
    samples: Deque[float] = field(default_factory=lambda: deque(maxlen=_WINDOW))

    def record(self, ms: float) -> None:
        self.samples.append(ms)

    def avg(self) -> float:
        return sum(self.samples) / len(self.samples) if self.samples else 0.0

    def p95(self) -> float:
        if not self.samples:
            return 0.0
        sorted_s = sorted(self.samples)
        idx = max(0, int(len(sorted_s) * 0.95) - 1)
        return sorted_s[idx]

    def count(self) -> int:
        return len(self.samples)


class PerformanceLogger:
    """
    Singleton metrics store.
    Thread-safe for asyncio (single-threaded event loop).
    """

    def __init__(self):
        # Latency series per mode (quick, deep, compare, etc.)
        self._mode_latency: Dict[str, _LatencySeries] = defaultdict(_LatencySeries)

        # Request counters
        self._request_counts: Dict[str, int] = defaultdict(int)
        self._total_requests: int = 0
        self._cache_hits: int = 0
        self._cache_misses: int = 0

        # LLM tracking
        self._llm_total_tokens: int = 0
        self._llm_total_cost_usd: float = 0.0
        self._llm_calls: int = 0

        # External API latency
        self._qdrant_latency: _LatencySeries = _LatencySeries()
        self._yfinance_latency: _LatencySeries = _LatencySeries()
        self._db_latency: _LatencySeries = _LatencySeries()

        # Start time
        self._started_at: float = time.time()

    # ── Recording methods ──────────────────────────────────────────────────

    def record_workflow(self, mode: str, duration_ms: float, cache_hit: bool = False) -> None:
        """Record a completed agent workflow execution."""
        self._mode_latency[mode].record(duration_ms)
        self._request_counts[mode] += 1
        self._total_requests += 1
        if cache_hit:
            self._cache_hits += 1
        else:
            self._cache_misses += 1
        logger.debug("Perf: mode=%s duration=%.0fms cache_hit=%s", mode, duration_ms, cache_hit)

    def record_llm(self, tokens_used: int, cost_usd: float) -> None:
        """Record an LLM call's token usage and cost."""
        self._llm_total_tokens += tokens_used
        self._llm_total_cost_usd += cost_usd
        self._llm_calls += 1

    def record_qdrant(self, duration_ms: float) -> None:
        self._qdrant_latency.record(duration_ms)

    def record_yfinance(self, duration_ms: float) -> None:
        self._yfinance_latency.record(duration_ms)

    def record_db(self, duration_ms: float) -> None:
        self._db_latency.record(duration_ms)

    # ── Snapshot ───────────────────────────────────────────────────────────

    def get_metrics_snapshot(self) -> dict:
        """Return a structured metrics snapshot for the /metrics endpoint."""
        uptime_s = time.time() - self._started_at
        per_mode = {}
        for mode, series in self._mode_latency.items():
            per_mode[mode] = {
                "avg_ms": round(series.avg(), 1),
                "p95_ms": round(series.p95(), 1),
                "total_calls": series.count(),
            }

        return {
            "uptime_seconds": round(uptime_s, 1),
            "total_requests": self._total_requests,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "cache_hit_rate_pct": round(
                (self._cache_hits / max(self._total_requests, 1)) * 100, 1
            ),
            "per_mode_latency": per_mode,
            "average_quick_mode_ms": round(self._mode_latency["quick"].avg(), 1),
            "average_deep_mode_ms": round(self._mode_latency["deep"].avg(), 1),
            "llm": {
                "total_calls": self._llm_calls,
                "total_tokens": self._llm_total_tokens,
                "total_cost_usd": round(self._llm_total_cost_usd, 6),
                "avg_cost_per_call": round(
                    self._llm_total_cost_usd / max(self._llm_calls, 1), 6
                ),
            },
            "external_apis": {
                "qdrant_avg_ms": round(self._qdrant_latency.avg(), 1),
                "yfinance_avg_ms": round(self._yfinance_latency.avg(), 1),
                "db_avg_ms": round(self._db_latency.avg(), 1),
            },
        }


# ── Module-level singleton ────────────────────────────────────────────────────
perf_logger = PerformanceLogger()
