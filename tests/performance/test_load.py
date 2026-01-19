"""
Load testing for Open Forge API.

Simulates multiple concurrent users performing various operations.
"""
import asyncio
import time
import random
from typing import List, Dict, Any
from dataclasses import dataclass, field

import pytest
import pytest_asyncio

from tests.performance.conftest import (
    PerformanceMetrics,
    async_timer,
    LOAD_TEST_USERS,
    LOAD_TEST_ITERATIONS,
)


pytestmark = [pytest.mark.performance, pytest.mark.load, pytest.mark.asyncio]


@dataclass
class LoadTestResults:
    """Aggregated results from a load test."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_duration: float = 0
    requests_per_second: float = 0
    error_rate: float = 0
    latencies: List[float] = field(default_factory=list)

    @property
    def mean_latency(self) -> float:
        return sum(self.latencies) / len(self.latencies) if self.latencies else 0

    @property
    def p95_latency(self) -> float:
        if not self.latencies:
            return 0
        sorted_lat = sorted(self.latencies)
        idx = int(len(sorted_lat) * 0.95)
        return sorted_lat[min(idx, len(sorted_lat) - 1)]

    @property
    def p99_latency(self) -> float:
        if not self.latencies:
            return 0
        sorted_lat = sorted(self.latencies)
        idx = int(len(sorted_lat) * 0.99)
        return sorted_lat[min(idx, len(sorted_lat) - 1)]

    def __str__(self) -> str:
        return (
            f"Load Test Results:\n"
            f"  Total requests: {self.total_requests}\n"
            f"  Successful: {self.successful_requests}\n"
            f"  Failed: {self.failed_requests}\n"
            f"  Duration: {self.total_duration:.2f}s\n"
            f"  Throughput: {self.requests_per_second:.2f} req/s\n"
            f"  Error rate: {self.error_rate:.2%}\n"
            f"  Mean latency: {self.mean_latency * 1000:.2f}ms\n"
            f"  P95 latency: {self.p95_latency * 1000:.2f}ms\n"
            f"  P99 latency: {self.p99_latency * 1000:.2f}ms"
        )


class VirtualUser:
    """Simulates a user making requests to the API."""

    def __init__(self, client, auth_headers: Dict[str, str], user_id: int):
        self.client = client
        self.auth_headers = auth_headers
        self.user_id = user_id
        self.request_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.latencies: List[float] = []

    async def health_check(self) -> bool:
        """Perform a health check request."""
        start = time.perf_counter()
        try:
            response = await self.client.get("/api/v1/health")
            self.latencies.append(time.perf_counter() - start)
            self.request_count += 1
            if response.status_code == 200:
                self.success_count += 1
                return True
            self.failure_count += 1
            return False
        except Exception:
            self.latencies.append(time.perf_counter() - start)
            self.request_count += 1
            self.failure_count += 1
            return False

    async def list_engagements(self) -> bool:
        """List engagements."""
        start = time.perf_counter()
        try:
            response = await self.client.get(
                "/api/v1/engagements",
                params={"page": 1, "page_size": 20},
                headers=self.auth_headers
            )
            self.latencies.append(time.perf_counter() - start)
            self.request_count += 1
            if response.status_code == 200:
                self.success_count += 1
                return True
            self.failure_count += 1
            return False
        except Exception:
            self.latencies.append(time.perf_counter() - start)
            self.request_count += 1
            self.failure_count += 1
            return False

    async def create_engagement(self) -> bool:
        """Create a new engagement."""
        start = time.perf_counter()
        try:
            payload = {
                "name": f"Load Test Engagement {self.user_id}-{self.request_count}",
                "description": "Created during load testing",
                "objective": "Test system under load",
                "priority": random.choice(["low", "medium", "high"]),
                "data_sources": [],
                "tags": ["load-test"],
                "requires_approval": False
            }
            response = await self.client.post(
                "/api/v1/engagements",
                json=payload,
                headers=self.auth_headers
            )
            self.latencies.append(time.perf_counter() - start)
            self.request_count += 1
            if response.status_code == 201:
                self.success_count += 1
                return True
            self.failure_count += 1
            return False
        except Exception:
            self.latencies.append(time.perf_counter() - start)
            self.request_count += 1
            self.failure_count += 1
            return False

    async def list_approvals(self) -> bool:
        """List approval requests."""
        start = time.perf_counter()
        try:
            response = await self.client.get(
                "/api/v1/approvals",
                params={"page": 1, "pending_only": True},
                headers=self.auth_headers
            )
            self.latencies.append(time.perf_counter() - start)
            self.request_count += 1
            if response.status_code == 200:
                self.success_count += 1
                return True
            self.failure_count += 1
            return False
        except Exception:
            self.latencies.append(time.perf_counter() - start)
            self.request_count += 1
            self.failure_count += 1
            return False

    async def run_scenario(self, iterations: int) -> None:
        """Run a realistic user scenario."""
        actions = [
            self.health_check,
            self.list_engagements,
            self.create_engagement,
            self.list_approvals,
        ]

        # Weight towards read operations
        weights = [1, 3, 1, 2]

        for _ in range(iterations):
            action = random.choices(actions, weights=weights, k=1)[0]
            await action()
            # Random think time between requests (10-100ms)
            await asyncio.sleep(random.uniform(0.01, 0.1))


class TestBasicLoadTests:
    """Basic load tests with configurable number of users."""

    async def test_10_concurrent_users(
        self,
        perf_test_client,
        auth_headers
    ):
        """Test with 10 concurrent users."""
        num_users = 10
        iterations_per_user = 20

        users = [
            VirtualUser(perf_test_client, auth_headers, i)
            for i in range(num_users)
        ]

        start_time = time.perf_counter()
        await asyncio.gather(*[
            user.run_scenario(iterations_per_user)
            for user in users
        ])
        total_duration = time.perf_counter() - start_time

        # Aggregate results
        results = LoadTestResults()
        results.total_duration = total_duration
        for user in users:
            results.total_requests += user.request_count
            results.successful_requests += user.success_count
            results.failed_requests += user.failure_count
            results.latencies.extend(user.latencies)

        results.requests_per_second = results.total_requests / total_duration
        results.error_rate = results.failed_requests / results.total_requests if results.total_requests > 0 else 0

        print(f"\n\n{results}")

        # Assertions
        assert results.error_rate < 0.05, f"Error rate too high: {results.error_rate:.2%}"
        assert results.p95_latency < 1.0, f"P95 latency too high: {results.p95_latency * 1000:.2f}ms"

    async def test_25_concurrent_users(
        self,
        perf_test_client,
        auth_headers
    ):
        """Test with 25 concurrent users."""
        num_users = 25
        iterations_per_user = 15

        users = [
            VirtualUser(perf_test_client, auth_headers, i)
            for i in range(num_users)
        ]

        start_time = time.perf_counter()
        await asyncio.gather(*[
            user.run_scenario(iterations_per_user)
            for user in users
        ])
        total_duration = time.perf_counter() - start_time

        # Aggregate results
        results = LoadTestResults()
        results.total_duration = total_duration
        for user in users:
            results.total_requests += user.request_count
            results.successful_requests += user.success_count
            results.failed_requests += user.failure_count
            results.latencies.extend(user.latencies)

        results.requests_per_second = results.total_requests / total_duration
        results.error_rate = results.failed_requests / results.total_requests if results.total_requests > 0 else 0

        print(f"\n\n{results}")

        # Slightly relaxed assertions for higher load
        assert results.error_rate < 0.1, f"Error rate too high: {results.error_rate:.2%}"
        assert results.p95_latency < 2.0, f"P95 latency too high: {results.p95_latency * 1000:.2f}ms"


class TestSustainedLoadTests:
    """Tests for sustained load over time."""

    async def test_sustained_low_load(
        self,
        perf_test_client,
        auth_headers
    ):
        """Test sustained low load (5 users) for extended period."""
        num_users = 5
        iterations_per_user = 50

        users = [
            VirtualUser(perf_test_client, auth_headers, i)
            for i in range(num_users)
        ]

        start_time = time.perf_counter()
        await asyncio.gather(*[
            user.run_scenario(iterations_per_user)
            for user in users
        ])
        total_duration = time.perf_counter() - start_time

        results = LoadTestResults()
        results.total_duration = total_duration
        for user in users:
            results.total_requests += user.request_count
            results.successful_requests += user.success_count
            results.failed_requests += user.failure_count
            results.latencies.extend(user.latencies)

        results.requests_per_second = results.total_requests / total_duration
        results.error_rate = results.failed_requests / results.total_requests if results.total_requests > 0 else 0

        print(f"\n\nSustained Low Load Test:")
        print(results)

        # Should maintain very low error rate under sustained low load
        assert results.error_rate < 0.01, f"Error rate too high: {results.error_rate:.2%}"


class TestRampUpLoadTests:
    """Tests with gradual ramp-up of load."""

    async def test_gradual_ramp_up(
        self,
        perf_test_client,
        auth_headers
    ):
        """Test with gradually increasing load."""
        max_users = 20
        iterations_per_user = 10
        ramp_steps = 4

        users_per_step = max_users // ramp_steps
        all_results: List[LoadTestResults] = []

        for step in range(1, ramp_steps + 1):
            num_users = users_per_step * step

            users = [
                VirtualUser(perf_test_client, auth_headers, i)
                for i in range(num_users)
            ]

            start_time = time.perf_counter()
            await asyncio.gather(*[
                user.run_scenario(iterations_per_user)
                for user in users
            ])
            total_duration = time.perf_counter() - start_time

            results = LoadTestResults()
            results.total_duration = total_duration
            for user in users:
                results.total_requests += user.request_count
                results.successful_requests += user.success_count
                results.failed_requests += user.failure_count
                results.latencies.extend(user.latencies)

            results.requests_per_second = results.total_requests / total_duration
            results.error_rate = results.failed_requests / results.total_requests if results.total_requests > 0 else 0

            all_results.append(results)

            print(f"\n\nStep {step} ({num_users} users):")
            print(f"  Throughput: {results.requests_per_second:.2f} req/s")
            print(f"  Error rate: {results.error_rate:.2%}")
            print(f"  P95 latency: {results.p95_latency * 1000:.2f}ms")

            # Brief pause between steps
            await asyncio.sleep(0.5)

        # Verify system degrades gracefully under increasing load
        # Error rate should increase slowly, not spike dramatically
        for i, results in enumerate(all_results):
            # Allow higher error rates at higher load, but not catastrophic
            max_error_rate = 0.02 * (i + 1)  # 2%, 4%, 6%, 8%
            assert results.error_rate < max_error_rate, (
                f"Step {i+1} error rate too high: {results.error_rate:.2%}"
            )


class TestSpecificScenarios:
    """Tests for specific usage scenarios."""

    async def test_read_heavy_workload(
        self,
        perf_test_client,
        auth_headers
    ):
        """Test with read-heavy workload (typical dashboard usage)."""
        num_users = 15

        async def read_heavy_user(user_id: int):
            """User that mostly reads."""
            metrics = {"reads": 0, "writes": 0, "latencies": []}

            for _ in range(30):
                start = time.perf_counter()

                # 90% reads, 10% writes
                if random.random() < 0.9:
                    await perf_test_client.get(
                        random.choice([
                            "/api/v1/health",
                            "/api/v1/engagements",
                            "/api/v1/approvals",
                        ]),
                        headers=auth_headers
                    )
                    metrics["reads"] += 1
                else:
                    await perf_test_client.post(
                        "/api/v1/engagements",
                        json={
                            "name": f"Read Heavy Test {user_id}",
                            "objective": "Test",
                            "priority": "low",
                        },
                        headers=auth_headers
                    )
                    metrics["writes"] += 1

                metrics["latencies"].append(time.perf_counter() - start)
                await asyncio.sleep(random.uniform(0.01, 0.05))

            return metrics

        start_time = time.perf_counter()
        results = await asyncio.gather(*[
            read_heavy_user(i) for i in range(num_users)
        ])
        total_duration = time.perf_counter() - start_time

        total_reads = sum(r["reads"] for r in results)
        total_writes = sum(r["writes"] for r in results)
        all_latencies = [lat for r in results for lat in r["latencies"]]

        print(f"\n\nRead-Heavy Workload Test:")
        print(f"  Total reads: {total_reads}")
        print(f"  Total writes: {total_writes}")
        print(f"  Read/Write ratio: {total_reads/total_writes if total_writes > 0 else 'N/A':.1f}:1")
        print(f"  Mean latency: {sum(all_latencies)/len(all_latencies)*1000:.2f}ms")
        print(f"  Throughput: {(total_reads + total_writes) / total_duration:.2f} req/s")

    async def test_write_heavy_workload(
        self,
        perf_test_client,
        auth_headers
    ):
        """Test with write-heavy workload (bulk creation scenario)."""
        num_users = 10

        async def write_heavy_user(user_id: int):
            """User that mostly writes."""
            success = 0
            failure = 0
            latencies = []

            for i in range(20):
                start = time.perf_counter()
                response = await perf_test_client.post(
                    "/api/v1/engagements",
                    json={
                        "name": f"Bulk Create {user_id}-{i}",
                        "description": f"Bulk creation test item {i}",
                        "objective": "Test write performance",
                        "priority": "medium",
                    },
                    headers=auth_headers
                )
                latencies.append(time.perf_counter() - start)

                if response.status_code == 201:
                    success += 1
                else:
                    failure += 1

                # Minimal delay between writes
                await asyncio.sleep(0.01)

            return {"success": success, "failure": failure, "latencies": latencies}

        start_time = time.perf_counter()
        results = await asyncio.gather(*[
            write_heavy_user(i) for i in range(num_users)
        ])
        total_duration = time.perf_counter() - start_time

        total_success = sum(r["success"] for r in results)
        total_failure = sum(r["failure"] for r in results)
        all_latencies = [lat for r in results for lat in r["latencies"]]

        print(f"\n\nWrite-Heavy Workload Test:")
        print(f"  Total writes: {total_success + total_failure}")
        print(f"  Successful: {total_success}")
        print(f"  Failed: {total_failure}")
        print(f"  Mean latency: {sum(all_latencies)/len(all_latencies)*1000:.2f}ms")
        print(f"  Throughput: {(total_success + total_failure) / total_duration:.2f} req/s")

        # Write operations should have reasonable success rate
        success_rate = total_success / (total_success + total_failure) if (total_success + total_failure) > 0 else 0
        assert success_rate > 0.95, f"Write success rate too low: {success_rate:.2%}"
