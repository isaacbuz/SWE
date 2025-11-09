/**
 * k6 Smoke Test Script
 * 
 * Lightweight smoke test for quick validation
 */

import http from 'k6/http';
import { check } from 'k6';

export const options = {
  vus: 1,
  duration: '1m',
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0'],
  },
};

const BASE_URL = __ENV.API_URL || 'http://localhost:8000';

export default function () {
  // Health check
  const healthResponse = http.get(`${BASE_URL}/health`);
  check(healthResponse, {
    'health check is 200': (r) => r.status === 200,
  });
  
  // API endpoint check
  const apiResponse = http.get(`${BASE_URL}/api/v1/tools`);
  check(apiResponse, {
    'API endpoint responds': (r) => r.status === 200 || r.status === 401,
  });
}

