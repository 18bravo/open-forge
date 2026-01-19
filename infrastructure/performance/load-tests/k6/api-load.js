/**
 * Open Forge API Load Test
 * k6 load testing script for the FastAPI backend
 *
 * Usage:
 *   k6 run api-load.js
 *   k6 run api-load.js --env BASE_URL=https://api.openforge.example.com
 *   k6 run api-load.js --env SCENARIO=stress
 *
 * Scenarios:
 *   - smoke: Quick validation (1 VU, 1 minute)
 *   - load: Standard load test (50 VUs, 10 minutes)
 *   - stress: Find breaking point (ramp to 200 VUs)
 *   - spike: Sudden traffic spike simulation
 *   - soak: Extended duration test (2 hours)
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';
import { randomString, randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';

// =============================================================================
// CONFIGURATION
// =============================================================================

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const API_TOKEN = __ENV.API_TOKEN || '';
const SCENARIO = __ENV.SCENARIO || 'load';

// Custom metrics
const engagementCreationTrend = new Trend('engagement_creation_duration');
const taskSubmissionTrend = new Trend('task_submission_duration');
const dataSourceQueryTrend = new Trend('datasource_query_duration');
const errorRate = new Rate('errors');
const requestsCounter = new Counter('total_requests');

// =============================================================================
// SCENARIOS
// =============================================================================

const scenarios = {
  smoke: {
    executor: 'constant-vus',
    vus: 1,
    duration: '1m',
  },
  load: {
    executor: 'ramping-vus',
    startVUs: 0,
    stages: [
      { duration: '2m', target: 25 },   // Ramp up
      { duration: '5m', target: 50 },   // Stay at 50 VUs
      { duration: '2m', target: 50 },   // Continue at 50 VUs
      { duration: '1m', target: 0 },    // Ramp down
    ],
    gracefulRampDown: '30s',
  },
  stress: {
    executor: 'ramping-vus',
    startVUs: 0,
    stages: [
      { duration: '2m', target: 50 },
      { duration: '5m', target: 100 },
      { duration: '5m', target: 150 },
      { duration: '5m', target: 200 },
      { duration: '2m', target: 0 },
    ],
    gracefulRampDown: '1m',
  },
  spike: {
    executor: 'ramping-vus',
    startVUs: 0,
    stages: [
      { duration: '30s', target: 10 },
      { duration: '30s', target: 200 }, // Spike!
      { duration: '1m', target: 200 },
      { duration: '30s', target: 10 },
      { duration: '2m', target: 10 },
      { duration: '30s', target: 0 },
    ],
  },
  soak: {
    executor: 'constant-vus',
    vus: 30,
    duration: '2h',
  },
};

export const options = {
  scenarios: {
    [SCENARIO]: scenarios[SCENARIO],
  },
  thresholds: {
    // HTTP request duration thresholds
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    // Specific endpoint thresholds
    'http_req_duration{name:health}': ['p(95)<100'],
    'http_req_duration{name:get_engagement}': ['p(95)<300'],
    'http_req_duration{name:create_engagement}': ['p(95)<1000'],
    'http_req_duration{name:submit_task}': ['p(95)<2000'],
    'http_req_duration{name:query_datasource}': ['p(95)<1500'],
    // Error rate threshold
    errors: ['rate<0.05'], // Less than 5% errors
    // Custom metric thresholds
    engagement_creation_duration: ['p(95)<1000'],
    task_submission_duration: ['p(95)<2000'],
  },
  // Output to InfluxDB or Prometheus (optional)
  // ext: {
  //   loadimpact: {
  //     projectID: 12345,
  //     name: 'Open Forge API Load Test',
  //   },
  // },
};

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

function getHeaders() {
  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-Request-ID': `k6-${randomString(16)}`,
  };
  if (API_TOKEN) {
    headers['Authorization'] = `Bearer ${API_TOKEN}`;
  }
  return headers;
}

function handleResponse(response, checkName) {
  requestsCounter.add(1);
  const success = check(response, {
    [`${checkName} status is 2xx`]: (r) => r.status >= 200 && r.status < 300,
    [`${checkName} has valid JSON`]: (r) => {
      try {
        JSON.parse(r.body);
        return true;
      } catch {
        return false;
      }
    },
  });
  if (!success) {
    errorRate.add(1);
    console.log(`Error in ${checkName}: Status ${response.status}, Body: ${response.body}`);
  } else {
    errorRate.add(0);
  }
  return success;
}

// =============================================================================
// TEST DATA GENERATORS
// =============================================================================

function generateEngagement() {
  return {
    name: `Load Test Engagement ${randomString(8)}`,
    description: `Created by k6 load test at ${new Date().toISOString()}`,
    client_name: `Test Client ${randomIntBetween(1, 100)}`,
    status: 'active',
    metadata: {
      test_run: true,
      created_by: 'k6',
      timestamp: Date.now(),
    },
  };
}

function generateAgentTask(engagementId) {
  return {
    engagement_id: engagementId,
    task_type: ['analysis', 'extraction', 'summarization'][randomIntBetween(0, 2)],
    input_data: {
      query: `Test query ${randomString(16)}`,
      context: `This is test context for load testing. ${randomString(100)}`,
    },
    priority: randomIntBetween(1, 5),
    options: {
      max_tokens: 1000,
      temperature: 0.7,
    },
  };
}

function generateDataSourceQuery(dataSourceId) {
  return {
    data_source_id: dataSourceId,
    query: `SELECT * FROM test_table WHERE id = ${randomIntBetween(1, 1000)}`,
    limit: 100,
    timeout_seconds: 30,
  };
}

// =============================================================================
// API ENDPOINT TESTS
// =============================================================================

function testHealthCheck() {
  group('Health Check', function () {
    const response = http.get(`${BASE_URL}/health`, {
      headers: getHeaders(),
      tags: { name: 'health' },
    });
    handleResponse(response, 'health');
  });
}

function testGetEngagements() {
  group('List Engagements', function () {
    const response = http.get(`${BASE_URL}/api/v1/engagements?limit=20&offset=0`, {
      headers: getHeaders(),
      tags: { name: 'list_engagements' },
    });
    handleResponse(response, 'list_engagements');
    return response;
  });
}

function testCreateEngagement() {
  let engagementId = null;

  group('Create Engagement', function () {
    const payload = JSON.stringify(generateEngagement());
    const startTime = Date.now();

    const response = http.post(`${BASE_URL}/api/v1/engagements`, payload, {
      headers: getHeaders(),
      tags: { name: 'create_engagement' },
    });

    engagementCreationTrend.add(Date.now() - startTime);

    if (handleResponse(response, 'create_engagement')) {
      try {
        const body = JSON.parse(response.body);
        engagementId = body.id;
      } catch (e) {
        console.log('Failed to parse engagement response');
      }
    }
  });

  return engagementId;
}

function testGetEngagement(engagementId) {
  if (!engagementId) return;

  group('Get Engagement', function () {
    const response = http.get(`${BASE_URL}/api/v1/engagements/${engagementId}`, {
      headers: getHeaders(),
      tags: { name: 'get_engagement' },
    });
    handleResponse(response, 'get_engagement');
  });
}

function testUpdateEngagement(engagementId) {
  if (!engagementId) return;

  group('Update Engagement', function () {
    const payload = JSON.stringify({
      name: `Updated Engagement ${randomString(8)}`,
      status: 'in_progress',
    });

    const response = http.patch(`${BASE_URL}/api/v1/engagements/${engagementId}`, payload, {
      headers: getHeaders(),
      tags: { name: 'update_engagement' },
    });
    handleResponse(response, 'update_engagement');
  });
}

function testSubmitAgentTask(engagementId) {
  if (!engagementId) return null;

  let taskId = null;

  group('Submit Agent Task', function () {
    const payload = JSON.stringify(generateAgentTask(engagementId));
    const startTime = Date.now();

    const response = http.post(`${BASE_URL}/api/v1/agents/tasks`, payload, {
      headers: getHeaders(),
      tags: { name: 'submit_task' },
      timeout: '30s',
    });

    taskSubmissionTrend.add(Date.now() - startTime);

    if (handleResponse(response, 'submit_task')) {
      try {
        const body = JSON.parse(response.body);
        taskId = body.task_id;
      } catch (e) {
        console.log('Failed to parse task response');
      }
    }
  });

  return taskId;
}

function testGetTaskStatus(taskId) {
  if (!taskId) return;

  group('Get Task Status', function () {
    const response = http.get(`${BASE_URL}/api/v1/agents/tasks/${taskId}`, {
      headers: getHeaders(),
      tags: { name: 'get_task_status' },
    });
    handleResponse(response, 'get_task_status');
  });
}

function testListDataSources() {
  let dataSources = [];

  group('List Data Sources', function () {
    const response = http.get(`${BASE_URL}/api/v1/datasources`, {
      headers: getHeaders(),
      tags: { name: 'list_datasources' },
    });

    if (handleResponse(response, 'list_datasources')) {
      try {
        const body = JSON.parse(response.body);
        dataSources = body.items || body || [];
      } catch (e) {
        console.log('Failed to parse datasources response');
      }
    }
  });

  return dataSources;
}

function testQueryDataSource(dataSourceId) {
  if (!dataSourceId) return;

  group('Query Data Source', function () {
    const payload = JSON.stringify(generateDataSourceQuery(dataSourceId));
    const startTime = Date.now();

    const response = http.post(`${BASE_URL}/api/v1/datasources/${dataSourceId}/query`, payload, {
      headers: getHeaders(),
      tags: { name: 'query_datasource' },
      timeout: '60s',
    });

    dataSourceQueryTrend.add(Date.now() - startTime);
    handleResponse(response, 'query_datasource');
  });
}

function testDeleteEngagement(engagementId) {
  if (!engagementId) return;

  group('Delete Engagement', function () {
    const response = http.del(`${BASE_URL}/api/v1/engagements/${engagementId}`, null, {
      headers: getHeaders(),
      tags: { name: 'delete_engagement' },
    });
    handleResponse(response, 'delete_engagement');
  });
}

// =============================================================================
// MAIN TEST FUNCTION
// =============================================================================

export default function () {
  // Health check
  testHealthCheck();
  sleep(randomIntBetween(1, 3));

  // Engagement CRUD operations
  const engagementId = testCreateEngagement();
  sleep(randomIntBetween(1, 2));

  testGetEngagements();
  sleep(randomIntBetween(1, 2));

  testGetEngagement(engagementId);
  sleep(randomIntBetween(1, 2));

  testUpdateEngagement(engagementId);
  sleep(randomIntBetween(1, 2));

  // Agent task operations
  const taskId = testSubmitAgentTask(engagementId);
  sleep(randomIntBetween(2, 5));

  testGetTaskStatus(taskId);
  sleep(randomIntBetween(1, 2));

  // Data source operations
  const dataSources = testListDataSources();
  sleep(randomIntBetween(1, 2));

  if (dataSources.length > 0) {
    const randomDataSource = dataSources[randomIntBetween(0, dataSources.length - 1)];
    testQueryDataSource(randomDataSource.id);
    sleep(randomIntBetween(1, 2));
  }

  // Cleanup - delete test engagement
  testDeleteEngagement(engagementId);
  sleep(randomIntBetween(1, 3));
}

// =============================================================================
// LIFECYCLE HOOKS
// =============================================================================

export function setup() {
  console.log(`Starting load test against ${BASE_URL}`);
  console.log(`Scenario: ${SCENARIO}`);

  // Verify the API is accessible
  const response = http.get(`${BASE_URL}/health`, {
    headers: getHeaders(),
  });

  if (response.status !== 200) {
    throw new Error(`API health check failed: ${response.status}`);
  }

  console.log('API health check passed');
  return { startTime: Date.now() };
}

export function teardown(data) {
  const duration = Date.now() - data.startTime;
  console.log(`Load test completed in ${Math.round(duration / 1000)} seconds`);
}

// =============================================================================
// HANDLE SUMMARY
// =============================================================================

export function handleSummary(data) {
  const summary = {
    timestamp: new Date().toISOString(),
    scenario: SCENARIO,
    base_url: BASE_URL,
    metrics: {
      http_reqs: data.metrics.http_reqs.values.count,
      http_req_duration_avg: data.metrics.http_req_duration.values.avg,
      http_req_duration_p95: data.metrics.http_req_duration.values['p(95)'],
      http_req_duration_p99: data.metrics.http_req_duration.values['p(99)'],
      errors: data.metrics.errors ? data.metrics.errors.values.rate : 0,
      vus_max: data.metrics.vus_max.values.max,
    },
  };

  return {
    'stdout': JSON.stringify(summary, null, 2),
    'results/api-load-summary.json': JSON.stringify(summary, null, 2),
  };
}
