/**
 * Open Forge Pipeline Load Test
 * k6 load testing script for Dagster pipeline operations
 *
 * Usage:
 *   k6 run pipeline-load.js
 *   k6 run pipeline-load.js --env DAGSTER_URL=https://dagster.openforge.example.com
 *   k6 run pipeline-load.js --env SCENARIO=concurrent
 *
 * Scenarios:
 *   - smoke: Quick validation
 *   - trigger: Pipeline triggering load test
 *   - concurrent: Concurrent run test
 *   - sensor: Sensor polling simulation
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter, Gauge } from 'k6/metrics';
import { randomString, randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';

// =============================================================================
// CONFIGURATION
// =============================================================================

const DAGSTER_URL = __ENV.DAGSTER_URL || 'http://localhost:3000';
const API_URL = __ENV.API_URL || 'http://localhost:8000';
const SCENARIO = __ENV.SCENARIO || 'trigger';

// Custom metrics
const pipelineTriggerTrend = new Trend('pipeline_trigger_duration');
const runStatusCheckTrend = new Trend('run_status_check_duration');
const graphqlQueryTrend = new Trend('graphql_query_duration');
const errorRate = new Rate('errors');
const activeRunsGauge = new Gauge('active_runs');
const runSuccessRate = new Rate('run_success_rate');

// =============================================================================
// SCENARIOS
// =============================================================================

const scenarios = {
  smoke: {
    executor: 'constant-vus',
    vus: 1,
    duration: '1m',
  },
  trigger: {
    executor: 'ramping-vus',
    startVUs: 0,
    stages: [
      { duration: '1m', target: 5 },
      { duration: '3m', target: 10 },
      { duration: '3m', target: 10 },
      { duration: '1m', target: 0 },
    ],
  },
  concurrent: {
    executor: 'constant-vus',
    vus: 20,
    duration: '10m',
  },
  sensor: {
    executor: 'constant-arrival-rate',
    rate: 10,
    timeUnit: '1s',
    duration: '5m',
    preAllocatedVUs: 10,
    maxVUs: 50,
  },
  stress: {
    executor: 'ramping-vus',
    startVUs: 0,
    stages: [
      { duration: '2m', target: 10 },
      { duration: '5m', target: 30 },
      { duration: '5m', target: 50 },
      { duration: '3m', target: 0 },
    ],
  },
};

export const options = {
  scenarios: {
    [SCENARIO]: scenarios[SCENARIO],
  },
  thresholds: {
    http_req_duration: ['p(95)<3000', 'p(99)<5000'],
    'http_req_duration{name:graphql}': ['p(95)<2000'],
    'http_req_duration{name:trigger_pipeline}': ['p(95)<5000'],
    'http_req_duration{name:get_run_status}': ['p(95)<1000'],
    errors: ['rate<0.1'],
    pipeline_trigger_duration: ['p(95)<5000'],
    run_status_check_duration: ['p(95)<1000'],
  },
};

// =============================================================================
// GRAPHQL QUERIES
// =============================================================================

const queries = {
  serverInfo: `
    query ServerInfoQuery {
      version
      serverTime
    }
  `,

  repositories: `
    query RepositoriesQuery {
      repositoriesOrError {
        ... on RepositoryConnection {
          nodes {
            id
            name
            location {
              name
            }
          }
        }
        ... on PythonError {
          message
        }
      }
    }
  `,

  jobs: `
    query JobsQuery($repositorySelector: RepositorySelector!) {
      repositoryOrError(repositorySelector: $repositorySelector) {
        ... on Repository {
          jobs {
            id
            name
            description
          }
        }
        ... on PythonError {
          message
        }
      }
    }
  `,

  launchPipelineExecution: `
    mutation LaunchPipelineExecution($executionParams: ExecutionParams!) {
      launchPipelineExecution(executionParams: $executionParams) {
        ... on LaunchRunSuccess {
          run {
            id
            runId
            status
          }
        }
        ... on PythonError {
          message
          stack
        }
        ... on InvalidStepError {
          invalidStepKey
        }
        ... on InvalidOutputError {
          outputName
        }
      }
    }
  `,

  runStatus: `
    query RunStatusQuery($runId: ID!) {
      runOrError(runId: $runId) {
        ... on Run {
          id
          runId
          status
          startTime
          endTime
          stats {
            ... on RunStatsSnapshot {
              stepsSucceeded
              stepsFailed
            }
          }
        }
        ... on PythonError {
          message
        }
        ... on RunNotFoundError {
          message
        }
      }
    }
  `,

  runs: `
    query RunsQuery($filter: RunsFilter, $limit: Int) {
      runsOrError(filter: $filter, limit: $limit) {
        ... on Runs {
          results {
            id
            runId
            status
            jobName
            startTime
            endTime
          }
          count
        }
        ... on PythonError {
          message
        }
      }
    }
  `,

  sensors: `
    query SensorsQuery($repositorySelector: RepositorySelector!) {
      sensorsOrError(repositorySelector: $repositorySelector) {
        ... on Sensors {
          results {
            id
            name
            sensorState {
              status
            }
          }
        }
        ... on PythonError {
          message
        }
      }
    }
  `,

  sensorTick: `
    query SensorTickQuery($sensorSelector: SensorSelector!) {
      sensorOrError(sensorSelector: $sensorSelector) {
        ... on Sensor {
          sensorState {
            ticks(limit: 10) {
              id
              status
              timestamp
            }
          }
        }
        ... on PythonError {
          message
        }
      }
    }
  `,
};

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

function getHeaders() {
  return {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };
}

function executeGraphQL(query, variables = {}, operationName = 'graphql') {
  const payload = JSON.stringify({
    query,
    variables,
  });

  const startTime = Date.now();
  const response = http.post(`${DAGSTER_URL}/graphql`, payload, {
    headers: getHeaders(),
    tags: { name: operationName },
  });

  graphqlQueryTrend.add(Date.now() - startTime);

  const success = check(response, {
    'GraphQL status is 200': (r) => r.status === 200,
    'GraphQL response has data': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.data !== undefined;
      } catch {
        return false;
      }
    },
    'GraphQL has no errors': (r) => {
      try {
        const body = JSON.parse(r.body);
        return !body.errors || body.errors.length === 0;
      } catch {
        return false;
      }
    },
  });

  if (!success) {
    errorRate.add(1);
    console.log(`GraphQL error (${operationName}): ${response.body}`);
  } else {
    errorRate.add(0);
  }

  return response;
}

function parseGraphQLResponse(response) {
  try {
    return JSON.parse(response.body);
  } catch {
    return null;
  }
}

// =============================================================================
// TEST DATA GENERATORS
// =============================================================================

function generatePipelineConfig() {
  return {
    resources: {
      io_manager: {
        config: {
          base_dir: '/tmp/dagster_test',
        },
      },
    },
    ops: {
      test_op: {
        config: {
          test_param: `load_test_${randomString(8)}`,
          iteration: randomIntBetween(1, 1000),
        },
      },
    },
  };
}

// =============================================================================
// PIPELINE TESTS
// =============================================================================

function testDagsterHealth() {
  group('Dagster Health', function () {
    const response = executeGraphQL(queries.serverInfo, {}, 'server_info');
    const body = parseGraphQLResponse(response);

    if (body && body.data) {
      console.log(`Dagster version: ${body.data.version}`);
    }
  });
}

function testListRepositories() {
  let repositories = [];

  group('List Repositories', function () {
    const response = executeGraphQL(queries.repositories, {}, 'list_repositories');
    const body = parseGraphQLResponse(response);

    if (body?.data?.repositoriesOrError?.nodes) {
      repositories = body.data.repositoriesOrError.nodes;
    }
  });

  return repositories;
}

function testListJobs(repositorySelector) {
  let jobs = [];

  group('List Jobs', function () {
    const response = executeGraphQL(
      queries.jobs,
      { repositorySelector },
      'list_jobs'
    );
    const body = parseGraphQLResponse(response);

    if (body?.data?.repositoryOrError?.jobs) {
      jobs = body.data.repositoryOrError.jobs;
    }
  });

  return jobs;
}

function testTriggerPipeline(jobName, repositorySelector) {
  let runId = null;

  group('Trigger Pipeline', function () {
    const executionParams = {
      selector: {
        repositoryLocationName: repositorySelector.repositoryLocationName,
        repositoryName: repositorySelector.repositoryName,
        jobName: jobName,
      },
      runConfigData: generatePipelineConfig(),
      mode: 'default',
    };

    const startTime = Date.now();
    const response = executeGraphQL(
      queries.launchPipelineExecution,
      { executionParams },
      'trigger_pipeline'
    );

    pipelineTriggerTrend.add(Date.now() - startTime);

    const body = parseGraphQLResponse(response);
    if (body?.data?.launchPipelineExecution?.run) {
      runId = body.data.launchPipelineExecution.run.runId;
      console.log(`Pipeline triggered: ${runId}`);
    }
  });

  return runId;
}

function testGetRunStatus(runId) {
  if (!runId) return null;

  let status = null;

  group('Get Run Status', function () {
    const startTime = Date.now();
    const response = executeGraphQL(
      queries.runStatus,
      { runId },
      'get_run_status'
    );

    runStatusCheckTrend.add(Date.now() - startTime);

    const body = parseGraphQLResponse(response);
    if (body?.data?.runOrError?.status) {
      status = body.data.runOrError.status;
    }
  });

  return status;
}

function testListRuns(limit = 20) {
  let runs = [];

  group('List Runs', function () {
    const response = executeGraphQL(
      queries.runs,
      { limit, filter: {} },
      'list_runs'
    );

    const body = parseGraphQLResponse(response);
    if (body?.data?.runsOrError?.results) {
      runs = body.data.runsOrError.results;

      // Count active runs
      const activeRuns = runs.filter(r =>
        ['STARTED', 'QUEUED', 'STARTING'].includes(r.status)
      ).length;
      activeRunsGauge.add(activeRuns);
    }
  });

  return runs;
}

function testListSensors(repositorySelector) {
  let sensors = [];

  group('List Sensors', function () {
    const response = executeGraphQL(
      queries.sensors,
      { repositorySelector },
      'list_sensors'
    );

    const body = parseGraphQLResponse(response);
    if (body?.data?.sensorsOrError?.results) {
      sensors = body.data.sensorsOrError.results;
    }
  });

  return sensors;
}

function testSensorPolling(sensorSelector) {
  group('Sensor Polling', function () {
    const response = executeGraphQL(
      queries.sensorTick,
      { sensorSelector },
      'sensor_tick'
    );

    const body = parseGraphQLResponse(response);
    if (body?.data?.sensorOrError?.sensorState?.ticks) {
      const ticks = body.data.sensorOrError.sensorState.ticks;
      console.log(`Sensor ticks: ${ticks.length}`);
    }
  });
}

function pollRunUntilComplete(runId, maxAttempts = 30, intervalSeconds = 2) {
  if (!runId) return null;

  let finalStatus = null;

  group('Poll Run Completion', function () {
    for (let i = 0; i < maxAttempts; i++) {
      const status = testGetRunStatus(runId);

      if (!status) {
        break;
      }

      if (['SUCCESS', 'FAILURE', 'CANCELED'].includes(status)) {
        finalStatus = status;
        if (status === 'SUCCESS') {
          runSuccessRate.add(1);
        } else {
          runSuccessRate.add(0);
        }
        break;
      }

      sleep(intervalSeconds);
    }
  });

  return finalStatus;
}

// =============================================================================
// API INTEGRATION TESTS
// =============================================================================

function testApiPipelineTrigger() {
  group('API Pipeline Trigger', function () {
    const payload = JSON.stringify({
      pipeline_name: 'test_pipeline',
      config: generatePipelineConfig(),
    });

    const response = http.post(`${API_URL}/api/v1/pipelines/trigger`, payload, {
      headers: getHeaders(),
      tags: { name: 'api_trigger_pipeline' },
    });

    check(response, {
      'API trigger status is 2xx': (r) => r.status >= 200 && r.status < 300,
    });
  });
}

// =============================================================================
// MAIN TEST FUNCTION
// =============================================================================

export default function () {
  // Health check
  testDagsterHealth();
  sleep(1);

  // Get repositories
  const repositories = testListRepositories();
  sleep(1);

  if (repositories.length === 0) {
    console.log('No repositories found, skipping job tests');
    sleep(5);
    return;
  }

  // Select first repository
  const repo = repositories[0];
  const repositorySelector = {
    repositoryName: repo.name,
    repositoryLocationName: repo.location?.name || repo.name,
  };

  // Get jobs
  const jobs = testListJobs(repositorySelector);
  sleep(1);

  // Get sensors
  const sensors = testListSensors(repositorySelector);
  sleep(1);

  // List recent runs
  testListRuns(20);
  sleep(1);

  // Trigger a pipeline if jobs exist
  if (jobs.length > 0) {
    const job = jobs[randomIntBetween(0, jobs.length - 1)];
    const runId = testTriggerPipeline(job.name, repositorySelector);
    sleep(2);

    // Check run status (don't wait for completion in load test)
    if (runId) {
      testGetRunStatus(runId);
    }
    sleep(1);
  }

  // Simulate sensor polling
  if (sensors.length > 0) {
    const sensor = sensors[0];
    const sensorSelector = {
      repositoryName: repo.name,
      repositoryLocationName: repo.location?.name || repo.name,
      sensorName: sensor.name,
    };
    testSensorPolling(sensorSelector);
    sleep(1);
  }

  // Random delay between iterations
  sleep(randomIntBetween(2, 5));
}

// =============================================================================
// LIFECYCLE HOOKS
// =============================================================================

export function setup() {
  console.log(`Starting pipeline load test against ${DAGSTER_URL}`);
  console.log(`Scenario: ${SCENARIO}`);

  // Verify Dagster is accessible
  const response = executeGraphQL(queries.serverInfo, {}, 'setup_health');

  if (response.status !== 200) {
    throw new Error(`Dagster health check failed: ${response.status}`);
  }

  const body = parseGraphQLResponse(response);
  if (body?.data?.version) {
    console.log(`Dagster version: ${body.data.version}`);
  }

  return { startTime: Date.now() };
}

export function teardown(data) {
  const duration = Date.now() - data.startTime;
  console.log(`Pipeline load test completed in ${Math.round(duration / 1000)} seconds`);
}

// =============================================================================
// HANDLE SUMMARY
// =============================================================================

export function handleSummary(data) {
  const summary = {
    timestamp: new Date().toISOString(),
    scenario: SCENARIO,
    dagster_url: DAGSTER_URL,
    metrics: {
      http_reqs: data.metrics.http_reqs?.values?.count || 0,
      http_req_duration_avg: data.metrics.http_req_duration?.values?.avg || 0,
      http_req_duration_p95: data.metrics.http_req_duration?.values?.['p(95)'] || 0,
      errors: data.metrics.errors?.values?.rate || 0,
      pipeline_trigger_p95: data.metrics.pipeline_trigger_duration?.values?.['p(95)'] || 0,
      graphql_query_avg: data.metrics.graphql_query_duration?.values?.avg || 0,
    },
  };

  return {
    'stdout': JSON.stringify(summary, null, 2),
    'results/pipeline-load-summary.json': JSON.stringify(summary, null, 2),
  };
}
