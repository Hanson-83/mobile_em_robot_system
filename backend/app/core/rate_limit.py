"""每 Token 简易滑动窗口限流（进程内；多实例演进 Redis）。"""

from __future__ import annotations

import time
from collections import defaultdict, deque

from app.core.errors import DomainError


class RateLimiter:
    def __init__(self, per_min: int = 60) -> None:
        self.per_min = per_min
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.time()
        window = 60.0
        q = self._hits[key]
        while q and now - q[0] > window:
            q.popleft()
        if len(q) >= self.per_min:
            raise DomainError("RATE_LIMITED", "超过每分钟请求上限")
        q.append(now)

    def reset(self) -> None:
        self._hits.clear()
