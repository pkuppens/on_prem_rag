/**
 * k6 load test for POST /api/ask (RAG question-answering).
 *
 * Prerequisites:
 * - Backend running on http://localhost:9180 (see docs/PORTS.md)
 * - k6 installed: https://k6.io/docs/get-started/installation/
 *
 * Run:
 *   k6 run scripts/load/ask-load.js
 *
 * Options (override via CLI):
 *   k6 run --vus 10 --duration 60s scripts/load/ask-load.js
 */
import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  vus: 5,
  duration: "30s",
  thresholds: {
    http_req_failed: ["rate<0.05"], // <5% failed
    http_req_duration: ["p(95)<15000"], // p95 < 15s (LLM can be slow)
  },
};

const BASE_URL = __ENV.BACKEND_URL || "http://localhost:9180";

export default function () {
  const payload = JSON.stringify({
    question: "What is the main topic of the documents?",
    top_k: 5,
  });

  const res = http.post(`${BASE_URL}/api/ask`, payload, {
    headers: { "Content-Type": "application/json" },
  });

  check(res, { "status 200": (r) => r.status === 200 });
  sleep(1);
}
