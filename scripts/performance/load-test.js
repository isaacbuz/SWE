/**
 * k6 Load Testing Script
 * 
 * Comprehensive load testing for SWE Platform API endpoints
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const apiDuration = new Trend('api_duration');
const requestCounter = new Counter('requests');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 50 },   // Ramp up to 50 users
    { duration: '5m', target: 50 },   // Stay at 50 users
    { duration: '2m', target: 100 },  // Ramp up to 100 users
    { duration: '5m', target: 100 },  // Stay at 100 users
    { duration: '2m', target: 200 },  // Ramp up to 200 users
    { duration: '5m', target: 200 },  // Stay at 200 users
    { duration: '2m', target: 0 },    // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'], // 95% < 500ms, 99% < 1s
    http_req_failed: ['rate<0.01'],                  // Error rate < 1%
    errors: ['rate<0.01'],                          // Custom error rate < 1%
  },
};

// Base URL
const BASE_URL = __ENV.API_URL || 'http://localhost:8000';

// Test data
const testUser = {
  email: 'test@example.com',
  password: 'testpassword123',
};

/**
 * Health check test
 */
export function healthCheck() {
  const response = http.get(`${BASE_URL}/health`);
  const success = check(response, {
    'health check status is 200': (r) => r.status === 200,
    'health check response time < 100ms': (r) => r.timings.duration < 100,
  });
  
  errorRate.add(!success);
  apiDuration.add(response.timings.duration);
  requestCounter.add(1);
  
  return success;
}

/**
 * API endpoints test
 */
export function testAPIEndpoints() {
  // Test tools endpoint
  const toolsResponse = http.get(`${BASE_URL}/api/v1/tools`, {
    headers: { 'Authorization': `Bearer ${__ENV.API_TOKEN || ''}` },
  });
  
  check(toolsResponse, {
    'tools endpoint status is 200': (r) => r.status === 200,
    'tools endpoint has data': (r) => JSON.parse(r.body).tools.length > 0,
  });
  
  errorRate.add(toolsResponse.status !== 200);
  apiDuration.add(toolsResponse.timings.duration);
  requestCounter.add(1);
  
  // Test projects endpoint
  const projectsResponse = http.get(`${BASE_URL}/api/v1/projects`, {
    headers: { 'Authorization': `Bearer ${__ENV.API_TOKEN || ''}` },
  });
  
  check(projectsResponse, {
    'projects endpoint status is 200': (r) => r.status === 200,
  });
  
  errorRate.add(projectsResponse.status !== 200);
  apiDuration.add(projectsResponse.timings.duration);
  requestCounter.add(1);
  
  sleep(1);
}

/**
 * Tool execution test
 */
export function testToolExecution() {
  const payload = JSON.stringify({
    toolName: 'github_create_issue',
    arguments: {
      repo: 'test/repo',
      title: 'Test Issue',
      body: 'This is a test issue',
    },
  });
  
  const response = http.post(
    `${BASE_URL}/api/v1/tools/execute`,
    payload,
    {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${__ENV.API_TOKEN || ''}`,
      },
    }
  );
  
  const success = check(response, {
    'tool execution status is 200': (r) => r.status === 200,
    'tool execution has result': (r) => {
      const body = JSON.parse(r.body);
      return body.success !== undefined;
    },
  });
  
  errorRate.add(!success);
  apiDuration.add(response.timings.duration);
  requestCounter.add(1);
  
  sleep(2);
}

/**
 * Main test function
 */
export default function () {
  // Health check (always run)
  healthCheck();
  
  // Randomly test different endpoints
  const testType = Math.random();
  
  if (testType < 0.5) {
    testAPIEndpoints();
  } else if (testType < 0.8) {
    testToolExecution();
  } else {
    // Just health check
    sleep(1);
  }
}

/**
 * Setup function (runs once before all VUs)
 */
export function setup() {
  // Optional: Authenticate and get token
  const loginResponse = http.post(`${BASE_URL}/api/v1/auth/login`, JSON.stringify(testUser), {
    headers: { 'Content-Type': 'application/json' },
  });
  
  if (loginResponse.status === 200) {
    const body = JSON.parse(loginResponse.body);
    return { token: body.token };
  }
  
  return { token: null };
}

/**
 * Teardown function (runs once after all VUs)
 */
export function teardown(data) {
  console.log('Load test completed');
  console.log(`Final token: ${data.token ? 'obtained' : 'not obtained'}`);
}

