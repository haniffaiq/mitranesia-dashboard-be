from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone


@dataclass
class LoginRateLimiter:
    max_attempts: int = 5
    window_seconds: int = 300
    attempts: dict[str, deque[datetime]] = field(default_factory=lambda: defaultdict(deque))

    def check(self, key: str) -> bool:
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(seconds=self.window_seconds)
        bucket = self.attempts[key]

        while bucket and bucket[0] < window_start:
            bucket.popleft()

        return len(bucket) < self.max_attempts

    def add_failure(self, key: str) -> None:
        self.attempts[key].append(datetime.now(timezone.utc))

    def reset(self, key: str) -> None:
        self.attempts.pop(key, None)
