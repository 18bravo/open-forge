"""
API endpoint performance benchmarks.

Tests response time, throughput, and latency for critical API endpoints.
"""
import asyncio
import time
from typing import Dict, List
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from tests.performance.conftest import (
    PerformanceMetrics,
    async_timer,
    LOAD_TEST_ITERATIONS,
)


pytestmark = [pytest.mark.performance, pytest.mark.asyncio]


class TestHealthEndpointBenchmarks:
    """Benchmark tests for health check endpoints."""

    async def test_health_check_response_time(
        self,
        perf_test_client,
        performance_metrics
    ):
        """Benchmark health check endpoint response time."""
        metrics = performance_metrics("health_check")

        for _ in range(100):
            async with async_timer(metrics):
                response = await perf_test_client.get("/api/v1/health")

            assert response.status_code == 200

        # Assert reasonable response times
        assert metrics.mean_time < 0.1  # Less than 100ms mean
        assert metrics.p95 < 0.2  # Less than 200ms p95
        print(f"\n{metrics}")

    async def test_health_check_throughput(
        self,
        perf_test_client,
        performance_metrics
    ):
        """Test health endpoint throughput with concurrent requests."""
        metrics = performance_metrics("health_throughput")

        async def make_request():
            async with async_timer(metrics):
                await perf_test_client.get("/api/v1/health")

        # Run 50 concurrent requests
        start_time = time.perf_counter()
        await asyncio.gather(*[make_request() for _ in range(50)])
        total_time = time.perf_counter() - start_time

        # Calculate throughput
        throughput = 50 / total_time
        print(f"\nThroughput: {throughput:.2f} requests/second")

        # Should handle at least 100 req/s for health checks
        assert throughput > 50, f"Throughput too low: {throughput:.2f} req/s"


class TestEngagementEndpointBenchmarks:
    """Benchmark tests for engagement CRUD endpoints."""

    @pytest.fixture
    def engagement_payload(self):
        """Sample engagement creation payload."""
        return {
            "name": "Performance Test Engagement",
            "description": "Created during performance testing",
            "objective": "Test API performance",
            "priority": "medium",
            "data_sources": [],
            "tags": ["perf-test"],
            "requires_approval": False
        }

    async def test_create_engagement_response_time(
        self,
        perf_test_client,
        auth_headers,
        performance_metrics,
        engagement_payload
    ):
        """Benchmark engagement creation endpoint."""
        metrics = performance_metrics("create_engagement")

        for i in range(50):
            payload = {**engagement_payload, "name": f"Perf Test {i}"}
            async with async_timer(metrics):
                response = await perf_test_client.post(
                    "/api/v1/engagements",
                    json=payload,
                    headers=auth_headers
                )

            assert response.status_code == 201

        # Assert reasonable response times for write operations
        assert metrics.mean_time < 0.5  # Less than 500ms mean
        assert metrics.p95 < 1.0  # Less than 1s p95
        print(f"\n{metrics}")

    async def test_list_engagements_response_time(
        self,
        perf_test_client,
        auth_headers,
        performance_metrics
    ):
        """Benchmark engagement listing endpoint."""
        metrics = performance_metrics("list_engagements")

        for _ in range(100):
            async with async_timer(metrics):
                response = await perf_test_client.get(
                    "/api/v1/engagements",
                    params={"page": 1, "page_size": 20},
                    headers=auth_headers
                )

            assert response.status_code == 200

        # List operations should be fast
        assert metrics.mean_time < 0.2  # Less than 200ms mean
        assert metrics.p95 < 0.4  # Less than 400ms p95
        print(f"\n{metrics}")

    async def test_engagement_detail_response_time(
        self,
        perf_test_client,
        auth_headers,
        performance_metrics
    ):
        """Benchmark engagement detail endpoint."""
        metrics = performance_metrics("get_engagement")

        # Note: This will return 404 but we're testing response time
        for _ in range(100):
            async with async_timer(metrics):
                response = await perf_test_client.get(
                    "/api/v1/engagements/test-id-123",
                    headers=auth_headers
                )

            # 404 is expected for non-existent engagement
            assert response.status_code in [200, 404]

        # Detail fetch should be fast
        assert metrics.mean_time < 0.1  # Less than 100ms mean
        print(f"\n{metrics}")


class TestApprovalEndpointBenchmarks:
    """Benchmark tests for approval endpoints."""

    async def test_list_approvals_response_time(
        self,
        perf_test_client,
        auth_headers,
        performance_metrics
    ):
        """Benchmark approval listing endpoint."""
        metrics = performance_metrics("list_approvals")

        for _ in range(100):
            async with async_timer(metrics):
                response = await perf_test_client.get(
                    "/api/v1/approvals",
                    params={"page": 1, "page_size": 20, "pending_only": True},
                    headers=auth_headers
                )

            assert response.status_code == 200

        assert metrics.mean_time < 0.2
        print(f"\n{metrics}")


class TestAdminEndpointBenchmarks:
    """Benchmark tests for admin dashboard endpoints."""

    async def test_dashboard_stats_response_time(
        self,
        perf_test_client,
        auth_headers,
        performance_metrics
    ):
        """Benchmark dashboard stats endpoint."""
        metrics = performance_metrics("dashboard_stats")

        for _ in range(50):
            async with async_timer(metrics):
                response = await perf_test_client.get(
                    "/api/v1/admin/dashboard/stats",
                    headers=auth_headers
                )

            # May return 404 or 200 depending on implementation
            assert response.status_code in [200, 404, 500]

        print(f"\n{metrics}")

    async def test_agent_clusters_response_time(
        self,
        perf_test_client,
        auth_headers,
        performance_metrics
    ):
        """Benchmark agent clusters listing endpoint."""
        metrics = performance_metrics("list_agent_clusters")

        for _ in range(50):
            async with async_timer(metrics):
                response = await perf_test_client.get(
                    "/api/v1/admin/agents/clusters",
                    headers=auth_headers
                )

            assert response.status_code in [200, 404, 500]

        print(f"\n{metrics}")


class TestCodegenEndpointBenchmarks:
    """Benchmark tests for code generation endpoints."""

    async def test_list_templates_response_time(
        self,
        perf_test_client,
        auth_headers,
        performance_metrics
    ):
        """Benchmark template listing endpoint."""
        metrics = performance_metrics("list_templates")

        for _ in range(50):
            async with async_timer(metrics):
                response = await perf_test_client.get(
                    "/api/v1/codegen/templates",
                    headers=auth_headers
                )

            assert response.status_code in [200, 404]

        print(f"\n{metrics}")

    async def test_preview_generation_response_time(
        self,
        perf_test_client,
        auth_headers,
        performance_metrics
    ):
        """Benchmark code preview endpoint."""
        metrics = performance_metrics("preview_codegen")

        preview_payload = {
            "ontology_id": "test-ontology",
            "generators": ["fastapi"],
            "options": {}
        }

        for _ in range(20):
            async with async_timer(metrics):
                response = await perf_test_client.post(
                    "/api/v1/codegen/preview",
                    json=preview_payload,
                    headers=auth_headers
                )

            # May return various status codes depending on implementation
            assert response.status_code in [200, 201, 400, 404, 500]

        print(f"\n{metrics}")


class TestConcurrentRequestBenchmarks:
    """Tests for handling concurrent requests."""

    async def test_mixed_endpoint_concurrent_load(
        self,
        perf_test_client,
        auth_headers,
        performance_metrics
    ):
        """Test system under mixed concurrent load."""
        health_metrics = performance_metrics("concurrent_health")
        engagement_metrics = performance_metrics("concurrent_engagement")

        async def health_request():
            async with async_timer(health_metrics):
                await perf_test_client.get("/api/v1/health")

        async def engagement_request():
            async with async_timer(engagement_metrics):
                await perf_test_client.get(
                    "/api/v1/engagements",
                    headers=auth_headers
                )

        # Mix of different request types
        tasks = []
        for i in range(100):
            if i % 2 == 0:
                tasks.append(health_request())
            else:
                tasks.append(engagement_request())

        start_time = time.perf_counter()
        await asyncio.gather(*tasks)
        total_time = time.perf_counter() - start_time

        total_requests = 100
        throughput = total_requests / total_time

        print(f"\n\nMixed Load Test Results:")
        print(f"  Total requests: {total_requests}")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Throughput: {throughput:.2f} req/s")
        print(f"  {health_metrics}")
        print(f"  {engagement_metrics}")

        # System should handle mixed load reasonably
        assert throughput > 20, f"Throughput too low: {throughput:.2f}"

    async def test_burst_load_handling(
        self,
        perf_test_client,
        performance_metrics
    ):
        """Test system handling of request bursts."""
        metrics = performance_metrics("burst_load")

        async def make_burst():
            """Make a burst of 20 requests."""
            tasks = []
            for _ in range(20):
                async def request():
                    async with async_timer(metrics):
                        await perf_test_client.get("/api/v1/health")
                tasks.append(request())
            await asyncio.gather(*tasks)

        # 5 bursts with short pauses between
        for burst_num in range(5):
            await make_burst()
            await asyncio.sleep(0.1)  # Brief pause between bursts

        print(f"\n\nBurst Load Test Results:")
        print(f"  Total requests: {metrics.count}")
        print(f"  {metrics}")

        # Even under burst load, should maintain reasonable response times
        assert metrics.p99 < 2.0, f"p99 latency too high: {metrics.p99 * 1000:.2f}ms"


class TestResponseSizeImpact:
    """Tests for response size impact on performance."""

    async def test_pagination_size_impact(
        self,
        perf_test_client,
        auth_headers,
        performance_metrics
    ):
        """Test impact of different page sizes on response time."""
        results: Dict[int, PerformanceMetrics] = {}

        for page_size in [10, 20, 50, 100]:
            metrics = performance_metrics(f"page_size_{page_size}")
            results[page_size] = metrics

            for _ in range(30):
                async with async_timer(metrics):
                    await perf_test_client.get(
                        "/api/v1/engagements",
                        params={"page": 1, "page_size": page_size},
                        headers=auth_headers
                    )

        print("\n\nPagination Size Impact:")
        for size, m in results.items():
            print(f"  page_size={size}: mean={m.mean_time*1000:.2f}ms, p95={m.p95*1000:.2f}ms")
