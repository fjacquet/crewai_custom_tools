"""Provider-keyed synchronous rate limiting for API-backed tools.

Ported from finwiz's async aiolimiter-based limiter and reduced to what the
sync ``@api_tool`` wrapper needs: a token bucket per provider, blocking
``acquire``. Providers are the same strings tools pass to ``@api_tool``.
Set ``CREWAI_TOOLS_RATE_LIMIT_DISABLED=1`` to bypass entirely (tests, CI).
"""

import os
import threading
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class RateLimit:
    """Token-bucket parameters for one provider."""

    requests_per_minute: int
    burst: int = 5


# Values ported from finwiz infrastructure/resilience/rate_limiter_config.py
DEFAULT_RATE_LIMITS: dict[str, RateLimit] = {
    "AlphaVantage": RateLimit(requests_per_minute=5, burst=2),
    "YahooFinance": RateLimit(requests_per_minute=600, burst=20),
    "TwelveData": RateLimit(requests_per_minute=8, burst=3),
    "ChartImg": RateLimit(requests_per_minute=30, burst=5),
    "CoinMarketCap": RateLimit(requests_per_minute=30, burst=5),
    "Kraken": RateLimit(requests_per_minute=60, burst=10),
    "SECEdgar": RateLimit(requests_per_minute=10, burst=3),
    "Perplexity": RateLimit(requests_per_minute=30, burst=5),
    "FRED": RateLimit(requests_per_minute=120, burst=20),
    "FearGreed": RateLimit(requests_per_minute=10, burst=2),
}

# env var -> (provider, premium limit); mirrors finwiz's premium-tier switches
_PREMIUM_OVERRIDES: dict[str, tuple[str, RateLimit]] = {
    "ALPHA_VANTAGE_PREMIUM": ("AlphaVantage", RateLimit(requests_per_minute=75, burst=10)),
    "TWELVE_DATA_PREMIUM": ("TwelveData", RateLimit(requests_per_minute=800, burst=50)),
}


class _TokenBucket:
    def __init__(self, limit: RateLimit) -> None:
        self._capacity = float(limit.burst)
        self._tokens = float(limit.burst)
        self._refill_per_sec = limit.requests_per_minute / 60.0
        self._updated = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        while True:
            with self._lock:
                now = time.monotonic()
                self._tokens = min(self._capacity, self._tokens + (now - self._updated) * self._refill_per_sec)
                self._updated = now
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
                wait = (1.0 - self._tokens) / self._refill_per_sec
            time.sleep(wait)


class RateLimiterRegistry:
    """Per-provider token buckets. Unknown providers pass through unthrottled."""

    def __init__(self, limits: dict[str, RateLimit] | None = None) -> None:
        base = dict(DEFAULT_RATE_LIMITS if limits is None else limits)
        for env_var, (provider, premium) in _PREMIUM_OVERRIDES.items():
            if provider in base and os.getenv(env_var, "false").lower() == "true":
                base[provider] = premium
        self._limits = base
        self._buckets = {provider: _TokenBucket(limit) for provider, limit in base.items()}

    def limit_for(self, provider: str) -> RateLimit | None:
        return self._limits.get(provider)

    def acquire(self, provider: str) -> None:
        if os.getenv("CREWAI_TOOLS_RATE_LIMIT_DISABLED", "").lower() in ("1", "true"):
            return
        bucket = self._buckets.get(provider)
        if bucket is not None:
            bucket.acquire()


_registry: RateLimiterRegistry | None = None
_registry_lock = threading.Lock()


def get_rate_limiter() -> RateLimiterRegistry:
    """Return the process-wide registry, creating it on first use."""
    global _registry
    if _registry is None:
        with _registry_lock:
            if _registry is None:
                _registry = RateLimiterRegistry()
    return _registry


def reset_rate_limiter() -> None:
    """Discard the singleton (tests only — premium env vars are read at creation)."""
    global _registry
    _registry = None
