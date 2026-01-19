"""
Shared fixtures for performance testing.
"""
import os
import asyncio
import time
import statistics
from typing import Dict, Any, List, Callable
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

import pytest
import pytest_asyncio


@dataclass
class PerformanceMetrics:
    """Container for performance test metrics."""

    name: str
    samples: List[float] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.samples)

    @property
    def min_time(self) -> float:
        return min(self.samples) if self.samples else 0

    @property
    def max_time(self) -> float:
        return max(self.samples) if self.samples else 0

    @property
    def mean_time(self) -> float:
        return statistics.mean(self.samples) if self.samples else 0

    @property
    def median_time(self) -> float:
        return statistics.median(self.samples) if self.samples else 0

    @property
    def stddev(self) -> float:
        return statistics.stdev(self.samples) if len(self.samples) > 1 else 0

    @property
    def p95(self) -> float:
        """95th percentile response time."""
        if not self.samples:
            return 0
        sorted_samples = sorted(self.samples)
        idx = int(len(sorted_samples) * 0.95)
        return sorted_samples[min(idx, len(sorted_samples) - 1)]

    @property
    def p99(self) -> float:
        """99th percentile response time."""
        if not self.samples:
            return 0
        sorted_samples = sorted(self.samples)
        idx = int(len(sorted_samples) * 0.99)
        return sorted_samples[min(idx, len(sorted_samples) - 1)]

    @property
    def requests_per_second(self) -> float:
        """Calculate throughput."""
        if not self.samples:
            return 0
        total_time = sum(self.samples)
        return len(self.samples) / total_time if total_time > 0 else 0

    def add_sample(self, duration: float) -> None:
        """Add a timing sample."""
        self.samples.append(duration)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "name": self.name,
            "count": self.count,
            "min_ms": round(self.min_time * 1000, 3),
            "max_ms": round(self.max_time * 1000, 3),
            "mean_ms": round(self.mean_time * 1000, 3),
            "median_ms": round(self.median_time * 1000, 3),
            "stddev_ms": round(self.stddev * 1000, 3),
            "p95_ms": round(self.p95 * 1000, 3),
            "p99_ms": round(self.p99 * 1000, 3),
            "rps": round(self.requests_per_second, 2),
        }

    def __str__(self) -> str:
        d = self.to_dict()
        return (
            f"{d['name']}: {d['count']} samples | "
            f"mean={d['mean_ms']}ms | p95={d['p95_ms']}ms | p99={d['p99_ms']}ms | "
            f"rps={d['rps']}"
        )


class PerformanceTimer:
    """Context manager for timing operations."""

    def __init__(self, metrics: PerformanceMetrics):
        self.metrics = metrics
        self.start_time: float = 0

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args):
        duration = time.perf_counter() - self.start_time
        self.metrics.add_sample(duration)


@asynccontextmanager
async def async_timer(metrics: PerformanceMetrics):
    """Async context manager for timing operations."""
    start_time = time.perf_counter()
    try:
        yield
    finally:
        duration = time.perf_counter() - start_time
        metrics.add_sample(duration)


@pytest.fixture
def performance_metrics():
    """Factory fixture for creating performance metrics."""
    metrics_store: Dict[str, PerformanceMetrics] = {}

    def _get_metrics(name: str) -> PerformanceMetrics:
        if name not in metrics_store:
            metrics_store[name] = PerformanceMetrics(name=name)
        return metrics_store[name]

    yield _get_metrics

    # Print summary at end of test
    if metrics_store:
        print("\n\n=== Performance Summary ===")
        for name, metrics in metrics_store.items():
            print(f"  {metrics}")


@pytest.fixture
def timer_factory(performance_metrics):
    """Factory fixture for creating timers."""
    def _create_timer(name: str) -> PerformanceTimer:
        return PerformanceTimer(performance_metrics(name))
    return _create_timer


# Environment configuration for performance tests
def get_perf_test_env() -> Dict[str, str]:
    """Get environment variables for performance testing."""
    return {
        "ENVIRONMENT": "performance-test",
        "DATABASE__HOST": os.environ.get("TEST_DB_HOST", "localhost"),
        "DATABASE__PORT": os.environ.get("TEST_DB_PORT", "5432"),
        "DATABASE__NAME": os.environ.get("TEST_DB_NAME", "openforge_test"),
        "DATABASE__USER": os.environ.get("TEST_DB_USER", "foundry"),
        "DATABASE__PASSWORD": os.environ.get("TEST_DB_PASSWORD", "foundry_dev"),
        "DATABASE__POOL_SIZE": "20",  # Larger pool for perf testing
        "REDIS__HOST": os.environ.get("TEST_REDIS_HOST", "localhost"),
        "REDIS__PORT": os.environ.get("TEST_REDIS_PORT", "6379"),
        "LLM__PROVIDER": "mock",
        "DEBUG": "false",
    }


@pytest.fixture(scope="session")
def perf_test_env():
    """Set up performance test environment."""
    env_vars = get_perf_test_env()
    original_env = {k: os.environ.get(k) for k in env_vars}

    os.environ.update(env_vars)

    yield env_vars

    for k, v in original_env.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


@pytest_asyncio.fixture
async def perf_test_client(perf_test_env):
    """Create a test client for performance testing."""
    from httpx import AsyncClient, ASGITransport
    from api.main import create_app

    app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        timeout=30.0
    ) as client:
        yield client


@pytest.fixture
def auth_headers():
    """Authentication headers for API requests."""
    return {
        "Authorization": "Bearer perf-test-token",
        "Content-Type": "application/json",
    }


# Test configuration
LOAD_TEST_USERS = int(os.environ.get("LOAD_TEST_USERS", "10"))
LOAD_TEST_ITERATIONS = int(os.environ.get("LOAD_TEST_ITERATIONS", "100"))
STRESS_TEST_USERS = int(os.environ.get("STRESS_TEST_USERS", "50"))
STRESS_TEST_DURATION_SECONDS = int(os.environ.get("STRESS_TEST_DURATION", "60"))


# Custom markers
def pytest_configure(config):
    """Configure custom pytest markers for performance tests."""
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "load: marks tests as load tests (multiple concurrent users)"
    )
    config.addinivalue_line(
        "markers", "stress: marks tests as stress tests (high load)"
    )
    config.addinivalue_line(
        "markers", "benchmark: marks tests as benchmark tests"
    )
