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
k6 run scripts/load/ask-load.js
```

Override options: `k6 run --vus 10 --duration 60s scripts/load/ask-load.js`

## SLOs (to be defined)

- Throughput: req/s for /api/ask
- Latency: p95 < N ms
