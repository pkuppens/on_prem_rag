# Load Testing

Created: 2026-02-23
Updated: 2026-04-06

Load-test scripts for the RAG backend.
See [docs/technical/TESTABILITY.md](../../docs/technical/TESTABILITY.md) for the full testing strategy.

## Files

| File | Tool | Purpose |
|------|------|--------|
| `ask-load.js` | k6 | Multi-endpoint load test (qa, retrieval, health) |
| `locustfile.py` | Locust | Alternative multi-endpoint load test |

## Endpoints exercised (API v1)

- `GET /api/v1/health`
- `POST /api/v1/retrieval/chunks` — retrieval-only
- `POST /api/v1/qa` — RAG (most expensive)

## Prerequisites

### k6

```bash
# macOS
brew install k6

# Linux (Debian/Ubuntu)
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
     --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" \
     | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update && sudo apt-get install k6

# Windows (Chocolatey)
choco install k6

# Docker
docker pull grafana/k6
```

See [k6.io/docs/get-started/installation](https://k6.io/docs/get-started/installation/) for other options.

### Locust (optional alternative)

```bash
# In project dev environment
uv add --dev locust

# Or standalone
pip install locust
```

## Quick Run

Ensure the backend is running on port 9180 first:

```bash
uv run start-backend          # or: docker-compose up
```

### k6

```bash
# Default: 5 virtual users, 30 s
k6 run scripts/load/ask-load.js

# Override VUs and duration
k6 run --vus 10 --duration 60s scripts/load/ask-load.js

# Target a different host
BACKEND_URL=http://staging:9180 k6 run scripts/load/ask-load.js
```

### Locust (headless)

```bash
locust -f scripts/load/locustfile.py \
    --host=http://localhost:9180 \
    --users 5 --spawn-rate 1 --run-time 30s --headless
```

### Locust (interactive UI)

```bash
locust -f scripts/load/locustfile.py --host=http://localhost:9180
# Open http://localhost:8089 in a browser, enter users/spawn-rate, click Start
```

## Target SLOs

Service-Level Objectives measured under a **steady load of 5 concurrent users**.

| Endpoint | p50 | p95 | Error rate |
|----------|-----|-----|------------|
| `GET /api/v1/health` | < 100 ms | < 500 ms | < 1 % |
| `POST /api/v1/retrieval/chunks` (retrieval-only) | < 500 ms | < 2 000 ms | < 1 % |
| `POST /api/v1/qa` (LLM inference) | < 5 000 ms | < 15 000 ms | < 5 % |

> **Note**: `/api/v1/qa` latency depends heavily on the Ollama model loaded and available
> hardware (CPU vs GPU). The 15 s p95 target assumes a small model (≤ 7 B parameters)
> on a typical developer workstation with no GPU.

## Throughput Targets

| Endpoint | Minimum req/s |
|----------|--------------|
| `GET /api/v1/health` | 20 |
| `POST /api/v1/retrieval/chunks` | 2 |
| `POST /api/v1/qa` | 0.5 |

## When to Run

- Before every **release** (manual sign-off step)
- After significant **model or embedding changes**
- When adding new retrieval strategies

CI integration is deliberately omitted because `/api/v1/qa` requires a running Ollama
model and can take minutes per run. To add it to CI, gate it on a dedicated
`[load-test]` label or schedule it as a nightly workflow.

## Interpreting Results

### k6 output

Key metrics to watch:

```
✓ http_req_failed.............: 0.00%   ✓ 0        ✗ 0
✓ http_req_duration...........: avg=1.2s p(90)=2.1s p(95)=2.8s
  { name:ask }................: avg=4.5s p(90)=9.8s p(95)=12.1s
  { name:query }...............: avg=0.4s p(90)=0.8s p(95)=1.1s
  { name:health }..............: avg=0.05s p(90)=0.08s p(95)=0.1s
```

A ✓ next to a threshold means the SLO was met; ✗ means it was violated.

### Locust output

The web UI at `http://localhost:8089` shows request stats in real time.
Export a CSV from the **Download Data** tab for post-run analysis.
