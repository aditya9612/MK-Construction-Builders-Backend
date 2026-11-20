"""Rate limiting and rapid duplicate submission protection for public reviews."""

from __future__ import annotations

import asyncio
import hashlib
import time
from collections import defaultdict
from dataclasses import dataclass, field

from app.core.exceptions import RateLimitExceededError, ValidationFailedError


@dataclass
class ReviewSubmissionTracker:
    """In-memory sliding-window rate limiter and duplicate detector."""

    # Maximum submissions allowed from a single IP within the window
    max_requests: int = 5
    # Window duration in seconds (5 minutes)
    window_seconds: int = 300
    # Window for exact duplicate submissions (2 minutes)
    duplicate_window_seconds: int = 120

    # IP -> list of timestamps
    _ip_history: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))
    # submission_hash -> timestamp
    _recent_hashes: dict[str, float] = field(default_factory=dict)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def _clean_ip_history(self, now: float, ip: str) -> None:
        threshold = now - self.window_seconds
        self._ip_history[ip] = [ts for ts in self._ip_history[ip] if ts > threshold]
        if not self._ip_history[ip]:
            self._ip_history.pop(ip, None)

    def _clean_hashes(self, now: float) -> None:
        threshold = now - self.duplicate_window_seconds
        expired = [h for h, ts in self._recent_hashes.items() if ts <= threshold]
        for h in expired:
            self._recent_hashes.pop(h, None)

    @staticmethod
    def compute_duplicate_hash(name: str, location: str, message: str) -> str:
        key = f"{name.strip().lower()}|{location.strip().lower()}|{message.strip().lower()}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    async def check_and_record(
        self,
        ip: str,
        name: str,
        location: str,
        message: str,
    ) -> None:
        """Check rate limits and duplicate submission; record if allowed."""
        now = time.time()
        dup_hash = self.compute_duplicate_hash(name, location, message)

        async with self._lock:
            self._clean_ip_history(now, ip)
            self._clean_hashes(now)

            # 1. Check duplicate rapid submission
            if dup_hash in self._recent_hashes:
                raise ValidationFailedError(
                    "Duplicate review detected. You have already submitted this review recently."
                )

            # 2. Check IP rate limit
            ip_requests = self._ip_history.get(ip, [])
            if len(ip_requests) >= self.max_requests:
                raise RateLimitExceededError(
                    f"Rate limit exceeded. Maximum {self.max_requests} submissions allowed every {self.window_seconds // 60} minutes."
                )

            # Record
            self._ip_history[ip].append(now)
            self._recent_hashes[dup_hash] = now

    async def reset(self) -> None:
        """Clear all rate limit state (useful for tests)."""
        async with self._lock:
            self._ip_history.clear()
            self._recent_hashes.clear()

    def sync_reset(self) -> None:
        """Synchronously clear all rate limit state."""
        self._ip_history.clear()
        self._recent_hashes.clear()


# Global tracker instance
_default_tracker = ReviewSubmissionTracker()


def get_review_tracker() -> ReviewSubmissionTracker:
    return _default_tracker
