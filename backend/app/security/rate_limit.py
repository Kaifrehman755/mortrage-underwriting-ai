"""Best-effort in-process rate limiting for public endpoints (F-05).

Phase 0 runs as a single process, so a fixed-count sliding-window counter keyed by client host
is sufficient to stop trivial request floods of the public reference-data endpoint. It is *not*
a substitute for an edge/gateway limiter (which is the documented recommendation for
production); see ``docs/security/access_policy.md``.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from app.core.config import Settings, get_settings

_registry_lock = threading.Lock()
_limiters: dict[int, SlidingWindowRateLimiter] = {}


class SlidingWindowRateLimiter:
    """Thread-safe sliding-window counter: at most ``limit`` hits per ``window_seconds``."""

    def __init__(self, limit: int, window_seconds: float = 60.0) -> None:
        self.limit = max(1, int(limit))
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        self._windows: dict[str, deque[float]] = {}

    def check(self, key: str) -> tuple[bool, int]:
        """Register a hit for ``key``; return ``(allowed, retry_after_seconds)``."""
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            window = self._windows.setdefault(key, deque())
            while window and window[0] <= cutoff:
                window.popleft()
            if len(window) >= self.limit:
                retry_after = max(1, int(round(self.window_seconds - (now - window[0]))))
                return False, retry_after
            window.append(now)
            return True, 0

    def reset(self) -> None:
        """Clear all counters (tests and long-lived processes)."""
        with self._lock:
            self._windows.clear()


def limiter_for(limit: int) -> SlidingWindowRateLimiter:
    """Return the shared limiter for a given limit (one instance per distinct limit)."""
    with _registry_lock:
        limiter = _limiters.get(limit)
        if limiter is None:
            limiter = SlidingWindowRateLimiter(limit)
            _limiters[limit] = limiter
        return limiter


def reset_rate_limiters() -> None:
    """Drop all shared limiters (used by regression tests)."""
    with _registry_lock:
        _limiters.clear()


async def enforce_rate_limit(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """FastAPI dependency enforcing the configured public-endpoint rate limit (F-05)."""
    limit = int(settings.RATE_LIMIT_PER_MINUTE)
    if limit <= 0:
        return

    key = request.client.host if request.client else "unknown"
    allowed, retry_after = limiter_for(limit).check(key)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please retry later.",
            headers={"Retry-After": str(retry_after)},
        )
