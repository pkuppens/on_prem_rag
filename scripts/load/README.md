# Load Testing

Created: 2026-02-23
Updated: 2026-02-23

Placeholder for load testing. See [docs/technical/TESTABILITY.md](../../docs/technical/TESTABILITY.md) for strategy.

## Tools

- **k6**: `brew install k6` or [k6.io](https://k6.io)
- **locust**: `uv add locust` (optional); `pip install locust` or use separate env

## Target Endpoints

- `POST /api/ask` — RAG (most expensive)
- `POST /api/documents/upload`
- `POST /api/query` — retrieval-only

## Quick Run (k6)

```bash
# Ensure backend is running on 9180
# k6 run ask-load.js
```

Create `ask-load.js` when implementing:

```javascript
// Example structure
import http from 'k6/http';
import { check, sleep } from 'k6';
export const options = {
  vus: 5,
  duration: '30s',
};
export default function () {
  const res = http.post('http://localhost:9180/api/ask', JSON.stringify({ question: 'test' }), {
    headers: { 'Content-Type': 'application/json' },
  });
  check(res, { 'status 200': (r) => r.status === 200 });
  sleep(1);
}
```

## SLOs (to be defined)

- Throughput: req/s for /api/ask
- Latency: p95 < N ms
