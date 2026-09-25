"""进程内 Token 限流（MVP）。超限返回 RATE_LIMITED。"""

from __future__ import annotations

import time
from collections import defaultdict, deque

from app.core.errors import rate_limited


class TokenRateLimiter:
    def __init__(self, per_min: int) -> None:
        self.per_min = per_min
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, token_key: str) -> None:
        now = time.monotonic()
        window = 60.0
        q = self._hits[token_key]
        while q and now - q[0] > window:
            q.popleft()
        if len(q) >= self.per_min:
            raise rate_limited(f"超过限流 {self.per_min} req/min")
        q.append(now)
