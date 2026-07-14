"""Shared test configuration for the central tools suite."""

import os

# Rate limiting is exercised explicitly in test_rate_limiter.py; everywhere
# else it must never slow a test down or make timing flaky.
os.environ.setdefault("CREWAI_TOOLS_RATE_LIMIT_DISABLED", "1")
