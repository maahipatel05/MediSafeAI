import time
import statistics
from collections import deque
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class LatencyTracker:
    """Rolling-window tracker for p50/p95/p99 latency, request volume, and grounding scores."""

    def __init__(self, window: int = 1000):
        self._latencies_ms: deque = deque(maxlen=window)
        self._request_count = 0
        self._error_count = 0
        self._grounding_scores: deque = deque(maxlen=window)

    def record_request(self, latency_ms: float, error: bool = False) -> None:
        self._latencies_ms.append(latency_ms)
        self._request_count += 1
        if error:
            self._error_count += 1

    def record_grounding(self, score: float) -> None:
        self._grounding_scores.append(score)

    def stats(self) -> dict:
        if not self._latencies_ms:
            return {
                "request_count": 0,
                "error_count": 0,
                "error_rate": 0.0,
                "latency_p50_ms": None,
                "latency_p95_ms": None,
                "latency_p99_ms": None,
                "avg_grounding_score": None,
            }

        sorted_lat = sorted(self._latencies_ms)

        def pct(data: list, p: float) -> float:
            idx = max(0, int(len(data) * p / 100) - 1)
            return round(data[idx], 1)

        return {
            "request_count": self._request_count,
            "error_count": self._error_count,
            "error_rate": round(self._error_count / max(self._request_count, 1), 4),
            "latency_p50_ms": pct(sorted_lat, 50),
            "latency_p95_ms": pct(sorted_lat, 95),
            "latency_p99_ms": pct(sorted_lat, 99),
            "avg_grounding_score": (
                round(statistics.mean(self._grounding_scores), 3)
                if self._grounding_scores
                else None
            ),
        }


tracker = LatencyTracker()


class LatencyMiddleware(BaseHTTPMiddleware):
    """Intercepts every request and records wall-clock latency + error flag."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        error = False
        try:
            response = await call_next(request)
            if response.status_code >= 500:
                error = True
            return response
        except Exception:
            error = True
            raise
        finally:
            tracker.record_request((time.perf_counter() - start) * 1000, error=error)
