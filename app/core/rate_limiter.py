"""
Simple in-memory rate limiter.
"""
import time
from collections import deque
from threading import Lock
from typing import Deque, Dict


class RateLimiter:
    """Fixed-window rate limiter (per-process, in-memory)."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, Deque[float]] = {}
        self._lock = Lock()

    def allow(self, identifier: str) -> bool:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            bucket = self._requests.get(identifier)
            if bucket is None:
                bucket = deque()
                self._requests[identifier] = bucket
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= self.max_requests:
                return False
            bucket.append(now)
            return True
