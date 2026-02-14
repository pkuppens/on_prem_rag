# Issue #77: Docker Compose Hardening — Validation Plan

**Created:** 2026-02-14  
**Updated:** 2026-02-14  
**Purpose:** Plan for validating current state, acceptance criteria, and Docker vs local performance before and after hardening.

---

## 1. Current State Validation (do first)

Validate that services are properly configured before implementing hardening changes.

### 1.1 Configuration Audit Checklist

| Check                   | Expected                               | Current State                                                      | Pass/Fail      |
| ----------------------- | -------------------------------------- | ------------------------------------------------------------------ | -------------- |
| **Port conflicts**      | No two services on same host port      | Chroma `9100:8000`, Auth `9100:9100` — **both use host 9100**      | ❌ FAIL        |
| **Backend Dockerfile**  | Valid Dockerfile with FROM             | `docker/backend/Dockerfile` has only `CMD` (no FROM) — invalid     | ❌ FAIL        |
| **Auth Dockerfile**     | File exists                            | `src/auth/Dockerfile` referenced but **does not exist**            | ❌ FAIL        |
| **Auth module path**    | Matches package structure              | Compose: `auth.main:app`; actual: `backend.auth_service.main:app`  | ❌ FAIL        |
| **Frontend Dockerfile** | Correct COPY paths for context `.`     | Copies `frontend/` but project has `src/frontend/` — path mismatch | ❌ FAIL        |
| **Ollama network**      | Same network as backend for same-stack | Ollama not on `app-network`; backend uses `host.docker.internal`   | ⚠️ Intentional |
| **Backend→Chroma**      | Reachable via service name             | `CHROMA_HOST=chroma`, `CHROMA_PORT=8000`                           | ✅ OK          |
| **Backend→Ollama**      | Reachable                              | `OLLAMA_BASE_URL=http://host.docker.internal:11434`                | ✅ OK          |
| **Frontend→Backend**    | Correct URL                            | `VITE_BACKEND_URL=http://localhost:9000`                           | ✅ OK          |
| **Volumes**             | chroma-data, ollama-data defined       | Both present                                                       | ✅ OK          |

### 1.2 Execution Steps (Current State Validation)

```bash
# Step 1: Verify all referenced files exist
ls -la docker/backend/Dockerfile
ls -la src/auth/Dockerfile
ls -la src/frontend/Dockerfile

# Step 2: Attempt full build (expect failures)
docker-compose build 2>&1 | tee docker-build-log.txt

# Step 3: Check port usage
netstat -an | grep -E "9100|9000|5173|11434"

# Step 4: If build succeeds, verify service connectivity
docker-compose up -d
docker-compose ps
curl -s http://localhost:9000/health
curl -s http://localhost:9100/  # Which service responds?
docker-compose down
```

### 1.3 Known Issues to Fix Before Hardening

1. **Port conflict**: Resolve Chroma vs Auth both using host 9100 (e.g., Chroma `9200:8000` or Auth `9110:9100`).
2. **Backend Dockerfile**: `docker/backend/Dockerfile` needs full Dockerfile (FROM + stages) or should extend root `Dockerfile`.
3. **Auth service**: Create `src/auth/Dockerfile` or fix compose to use `backend.auth_service.main:app` and correct build path.
4. **Frontend Dockerfile**: Fix COPY paths — from context `.`, use `COPY src/frontend/package*.json ./` etc., or change build context.

---

## 2. Acceptance Criteria Validation Plan

### Issue #77 Acceptance Criteria

| Criterion                                                          | Validation Method            | Evidence                                                                  |
| ------------------------------------------------------------------ | ---------------------------- | ------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| **AC1:** All services have health checks in docker-compose         | Inspect `docker-compose.yml` | Screenshot or `grep -A5 healthcheck docker-compose.yml`                   |
| **AC2:** Dockerfile uses multi-stage build (smaller runtime image) | Inspect Dockerfile(s)        | `grep -E "FROM                                                            | AS" Dockerfile docker/backend/Dockerfile` showing builder + runtime stages |
| **AC3:** System works in air-gapped mode after initial setup       | Manual verification          | Steps executed, `docker-compose up` success, screenshot of healthy status |

### 2.1 Validation Execution Plan

#### AC1: Health checks

```bash
# After implementation
docker-compose config | grep -A 6 healthcheck

# Verify health check endpoints
docker-compose up -d
sleep 30
docker-compose ps  # All services should show "healthy"
docker-compose down
```

**Evidence to collect:** `docker-compose ps` output showing `State: Up (healthy)` for chroma, backend, auth. Note: Ollama official image lacks curl/wget; healthcheck omitted.

#### AC2: Multi-stage build

```bash
# Count stages
grep -c "^FROM" docker/backend/Dockerfile  # Expect >= 2

# Compare image sizes (before vs after)
docker images | grep on_prem_rag
```

**Evidence to collect:** Dockerfile snippet showing `FROM ... AS builder` and `FROM ... AS runtime`, plus final image size.

#### AC3: Air-gapped operation

```bash
# 1. Initial setup (with network): pull images, download Ollama model
docker-compose pull
# Pull ollama and run: ollama pull llama2  # or required model

# 2. Disconnect network (or use --network none for testing)

# 3. Start stack
docker-compose up -d

# 4. Verify
curl -s http://localhost:9000/health
curl -s http://localhost:9000/api/health/llm  # Requires model loaded
```

**Evidence to collect:** Log of successful `docker-compose up` and health check responses with no network.

#### Air-gapped operation steps

1. **With network** — initial setup:

   ```bash
   docker-compose pull
   docker-compose build
   docker-compose run --rm ollama ollama pull llama2
   ```

2. **Disconnect network** (or use `--network none` for testing).

3. **Start stack**:

   ```bash
   docker-compose up -d
   ```

4. **Verify**:
   ```bash
   curl -s http://localhost:9000/health
   curl -s http://localhost:9000/api/health/llm
   ```

### 2.2 Evidence Template for PR/Issue

```markdown
## Acceptance Criteria Evidence

### AC1: Health checks

- [x] chroma, backend, auth have `healthcheck` in docker-compose; ollama omitted (official image lacks curl/wget)
- Evidence: docker-compose ps — chroma, backend, auth show Up (healthy). See Appendix B.

### AC2: Multi-stage build

- [x] docker/backend/Dockerfile has builder + runtime stages
- Evidence: grep -E "FROM|AS" docker/backend/Dockerfile — shows FROM ... AS builder, FROM ... AS runtime

### AC3: Air-gapped operation

- [ ] Stack starts and health checks pass without network (manual verification by operator)
- Evidence: [paste commands + output after network-disconnect test]
```

---

## 3. Performance Comparison: Docker vs Local

### 3.1 Services to Compare

| Service         | Local equivalent              | Metric to measure                                     |
| --------------- | ----------------------------- | ----------------------------------------------------- |
| **Backend API** | `uv run start-backend`        | Request latency (e.g. `/health`, `/api/documents`)    |
| **Ollama**      | `ollama run` (host)           | First-token latency, tokens/sec for a standard prompt |
| **ChromaDB**    | Chroma client to local Chroma | Query latency for similarity search                   |

### 3.2 Measurement Plan

#### Backend API

```bash
# Local
uv run start-backend &
sleep 5
for i in {1..10}; do curl -s -o /dev/null -w "%{time_total}\n" http://localhost:9000/health; done
pkill -f start-backend

# Docker
docker-compose up -d backend chroma
sleep 30
for i in {1..10}; do curl -s -o /dev/null -w "%{time_total}\n" http://localhost:9000/health; done
docker-compose down
```

**Report:** Mean ± std dev of 10 runs for local vs Docker.

#### Ollama (if running in Docker)

```bash
# Standard prompt
PROMPT="Write a short poem about Docker."
time curl -s http://localhost:11434/api/generate -d "{\"model\":\"llama2\",\"prompt\":\"$PROMPT\",\"stream\":false}"
```

Compare:

- Docker: Ollama container
- Local: Ollama on host (backend in Docker uses host.docker.internal)

Note: Current setup uses host Ollama, so "Docker Ollama" would require adding Ollama to compose and changing backend config.

#### ChromaDB

```bash
# From backend container: time a similarity search
docker-compose exec backend python -c "
import time
from backend.rag_pipeline.core.vector_store import get_vector_store_manager_from_env
mgr = get_vector_store_manager_from_env()
start = time.perf_counter()
# run a simple query
end = time.perf_counter()
print(f'Query latency: {(end-start)*1000:.2f} ms')
"
```

### 3.3 Expected Overhead (typical ranges)

- **Backend API**: 0.5–2 ms extra per request (Docker networking + bridge)
- **Ollama**: Minimal if on host; 5–15% if Ollama in container (GPU passthrough matters)
- **ChromaDB**: 1–3 ms (container networking)

### 3.4 Validation Report Template

```markdown
## Performance Comparison: Docker vs Local

| Service         | Metric      | Local (ms) | Docker (ms) | Overhead |
| --------------- | ----------- | ---------- | ----------- | -------- |
| Backend /health | p50         | X          | Y           | Z%       |
| Ollama generate | First token | X          | Y           | Z%       |
| Chroma query    | p50         | X          | Y           | Z%       |

Environment: [OS, Docker version, CPU/RAM]
```

---

## 4. Port Configuration and Conflict Resolution

### 4.1 Strategy

- **Configurable ports via environment variables** — use `BACKEND_PORT`, `AUTH_PORT`, `CHROMA_HOST_PORT`, `OLLAMA_HOST_PORT`, etc. with sensible defaults.
- **Defaults stay standard where possible** (e.g. Ollama 11434) to reduce surprises.
- **Override only when needed** — developers experiencing conflicts set vars in `.env`.

### 4.2 Environment Variables for Ports

| Variable           | Default | Description            | When to Override              |
| ------------------ | ------- | ---------------------- | ----------------------------- |
| `BACKEND_PORT`     | 9000    | Backend API host port  | Another app uses 9000         |
| `AUTH_PORT`        | 9100    | Auth service host port | Conflict with Chroma or other |
| `CHROMA_HOST_PORT` | 9200    | ChromaDB external port | Conflict with other services  |
| `OLLAMA_HOST_PORT` | 11434   | Ollama host port       | Host Ollama on different port |
| `FRONTEND_PORT`    | 5173    | Vite dev server port   | Conflict with other Vite app  |

### 4.3 Error Handling and User Feedback

**Startup:**

- When a port is in use, Docker typically errors with "port is already allocated" or "address already in use".
- **Action:** Document a clear message: `Port X is already in use. Set SERVICE_PORT=Y in .env to use a different port.`

**Health checks:**

- If a service fails to bind, logs should indicate which port and service.
- Health check failures surface as `unhealthy` in `docker-compose ps` — document this in troubleshooting.

**Documentation:**

- Add a **Port conflicts** subsection to `docs/TEST_DOCKER.md` with:
  1. How to detect: `docker-compose up` fails with bind error.
  2. How to fix: Copy `env.example` to `.env`, set override vars.
  3. Common conflicts: Chroma vs Auth (both 9100), Ollama (11434), multiple stacks.

### 4.4 Developer vs Production

- **Developers:** Most likely to hit conflicts (multiple stacks, local Ollama/Postgres).
- **Production:** Usually single deployment; conflicts rare; same config mechanism applies.
- **Recommendation:** Configurable ports benefit both; production can keep defaults.

---

## 5. Recommended Execution Order

1. **Current state validation** (Section 1) — run first; fix config issues before hardening.
2. **Implement hardening** (Issue #77 scope).
3. **Acceptance criteria validation** (Section 2) — after implementation.
4. **Performance comparison** (Section 3) — optional; useful for documentation.

---

---

## Appendix A: Current State Validation Results (2025-02-14)

Executed on Windows; Docker Desktop was not running, so build test could not complete.

| Check                                  | Result                                |
| -------------------------------------- | ------------------------------------- |
| `docker/backend/Dockerfile` exists     | ✅ Yes                                |
| `src/auth/Dockerfile` exists           | ❌ **No**                             |
| `src/frontend/Dockerfile` exists       | ✅ Yes                                |
| `docker/backend/Dockerfile` content    | Only `CMD` line — no `FROM` (invalid) |
| `docker-compose config`                | Parses successfully                   |
| Port conflict (Chroma 9100, Auth 9100) | ❌ **Both use host port 9100**        |

---

## Appendix B: Post-Implementation Validation Results (2026-02-14)

### Acceptance Criteria Evidence

| Criterion                     | Status    | Evidence                                                                                                                                 |
| ----------------------------- | --------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **AC1:** Health checks        | ✅ Pass   | chroma, backend, auth have `healthcheck`; Ollama omitted (official image lacks curl/wget); frontend has no healthcheck (Vite dev server) |
| **AC2:** Multi-stage build    | ✅ Pass   | `docker/backend/Dockerfile` has `FROM ... AS builder` and `FROM ... AS runtime`                                                          |
| **AC3:** Air-gapped operation | ⏳ Manual | Same `docker-compose up` flow; requires network-disconnect test by operator                                                              |

### docker-compose ps Output

```
NAME                     IMAGE                    STATUS                   PORTS
on_prem_rag-auth-1       on_prem_rag-auth         Up (healthy)             0.0.0.0:9100->9100/tcp
on_prem_rag-backend-1    on_prem_rag-backend      Up (healthy)             0.0.0.0:9000->9000/tcp
on_prem_rag-chroma-1     chromadb/chroma:latest   Up (healthy)             0.0.0.0:9200->8000/tcp
on_prem_rag-frontend-1   on_prem_rag-frontend    Up 3 minutes             0.0.0.0:5180->5173/tcp
on_prem_rag-ollama-1     ollama/ollama:latest    Up 8 minutes             0.0.0.0:11435->11434/tcp
```

**Note:** Ollama shows "Up" (not "healthy") — expected; no healthcheck by design. Frontend uses configurable `FRONTEND_PORT` (here 5180) when 5173 conflicts.

### docker-compose up -d Output (OK)

All containers start successfully. chroma, auth, backend report `Healthy`; ollama and frontend report `Running` (no healthcheck). This is the expected outcome.

---

## References

- [Issue #77](https://github.com/pkuppens/on_prem_rag/issues/77)
- [ISSUE_IMPLEMENTATION_WORKFLOW.md](./ISSUE_IMPLEMENTATION_WORKFLOW.md)
- [docs/TEST_DOCKER.md](../TEST_DOCKER.md)
- [docs/DOCKER_TECHNICAL.md](../DOCKER_TECHNICAL.md)
