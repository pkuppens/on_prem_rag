/**
 * k6 load test for the RAG backend (POST /api/ask, POST /api/query, GET /api/health).
 *
 * Prerequisites:
 * - Backend running on http://localhost:9180 (see docs/PORTS.md)
 * - k6 installed: https://k6.io/docs/get-started/installation/
 *
 * Quick run (default: 5 VUs, 30 s):
 *   k6 run scripts/load/ask-load.js
 *
 * Override options via CLI:
 *   k6 run --vus 10 --duration 60s scripts/load/ask-load.js
 *
 * Override target host:
 *   BACKEND_URL=http://my-server:9180 k6 run scripts/load/ask-load.js
 *
 * SLOs (Service-Level Objectives):
 *   - POST /api/ask   : p95 < 15 000 ms, error rate < 5 %  (LLM inference included)
 *   - POST /api/query : p95 <  2 000 ms, error rate < 1 %  (retrieval-only)
 *   - GET  /api/health: p95 <    500 ms, error rate < 1 %
 */

import http from "k6/http";
import { check, group, sleep } from "k6";

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------
export const options = {
  vus: 5,
  duration: "30s",
  thresholds: {
    // Global error rate
    http_req_failed: ["rate<0.05"],

    // Per-endpoint latency SLOs (tagged via http.post/get name parameter)
    "http_req_duration{name:ask}": ["p(95)<15000"],
    "http_req_duration{name:query}": ["p(95)<2000"],
    "http_req_duration{name:health}": ["p(95)<500"],
  },
};

const BASE_URL = __ENV.BACKEND_URL || "http://localhost:9180";

const JSON_HEADERS = { "Content-Type": "application/json" };

// Sample questions exercising different retrieval paths
const ASK_QUESTIONS = [
  "What is the main topic of the documents?",
  "Summarise the key findings.",
  "What recommendations are made?",
  "Are there any risks mentioned?",
  "What conclusions can be drawn?",
];

const QUERY_TEXTS = [
  "treatment guidelines",
  "diagnostic criteria",
  "patient safety",
  "evidence-based recommendations",
  "clinical outcomes",
];

// ---------------------------------------------------------------------------
// Helper: pick a random element from an array
// ---------------------------------------------------------------------------
function randomFrom(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

// ---------------------------------------------------------------------------
// Default scenario: mix of all three endpoints in each VU iteration
// ---------------------------------------------------------------------------
export default function () {
  // 1. Health check (lightweight, always included)
  group("health", () => {
    const res = http.get(`${BASE_URL}/api/health`, { tags: { name: "health" } });
    check(res, {
      "health status 200": (r) => r.status === 200,
    });
  });

  sleep(0.5);

  // 2. Retrieval-only query (cheaper, no LLM)
  group("query", () => {
    const payload = JSON.stringify({
      query: randomFrom(QUERY_TEXTS),
      top_k: 5,
    });
    const res = http.post(`${BASE_URL}/api/query`, payload, {
      headers: JSON_HEADERS,
      tags: { name: "query" },
    });
    check(res, {
      "query status 200": (r) => r.status === 200,
    });
  });

  sleep(0.5);

  // 3. Full RAG ask (most expensive — LLM included)
  group("ask", () => {
    const payload = JSON.stringify({
      question: randomFrom(ASK_QUESTIONS),
      top_k: 5,
      similarity_threshold: 0.7,
    });
    const res = http.post(`${BASE_URL}/api/ask`, payload, {
      headers: JSON_HEADERS,
      tags: { name: "ask" },
    });
    check(res, {
      "ask status 200": (r) => r.status === 200,
    });
  });

  sleep(1);
}
