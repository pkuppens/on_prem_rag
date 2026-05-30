# k8s — Kubernetes manifests for on_prem_rag

Kubernetes deployment of the on-prem RAG stack, derived from `docker-compose.yml`
and the generic building blocks in [`pkuppens/ckad-catalog`](https://github.com/pkuppens/ckad-catalog).
Tracks pkuppens/pkuppens#116 (EPIC pkuppens/pkuppens#109).

## Services

| Manifest | Workload | State | Notes |
| --- | --- | --- | --- |
| `chroma.yaml` | ChromaDB vector store | Stateful (PVC) | TCP probes |
| `ollama.yaml` | Ollama LLM runtime | Stateful (PVC) | GPU optional (see comments) |
| `backend.yaml` | RAG FastAPI backend | Stateless + uploads PVC | `/health` probes, **HPA** |
| `auth.yaml` | Auth FastAPI service | Stateless | `/oauth/providers` probe |
| `frontend.yaml` | React/Vite UI | Stateless | served on 5173 |
| `ingress.yaml` | Ingress | - | `/` -> frontend, `/api` -> backend, `/auth` -> auth |

Config in `configmap.yaml`; LLM keys/JWT secret in `secret.yaml` (PLACEHOLDERS — never commit real values).

## Deploy (local kind)

```powershell
# build + load images (no registry needed for kind)
docker build -t onpremrag-backend:dev -f docker/backend/Dockerfile .
docker build -t onpremrag-frontend:dev -f docker/frontend/Dockerfile .
kind load docker-image onpremrag-backend:dev onpremrag-frontend:dev --name ckad

kubectl apply -k k8s
kubectl get pods -n onpremrag
curl -H "Host: onpremrag.local" http://localhost/
```

## Scaling showcase

`backend.yaml` ships a HorizontalPodAutoscaler (CPU 70%, 2-6 replicas) so the API
tier scales independently. This is the CKAD scaling demonstration.

### Follow-up: extract embeddings/STT into a microservice (planned)

Today embeddings and Whisper STT run **in-process** inside the backend (memory/GPU
heavy). The next step (tracked in pkuppens/pkuppens#116, advanced) is to extract
them into their own Deployment + Service so they scale and (optionally) schedule on
GPU nodes independently of the API:

- New `embeddings` Deployment exposing an internal embedding endpoint; backend calls
  it over HTTP instead of importing the model.
- Its own HPA and optional GPU `nodeSelector`/`tolerations` + `resources.limits.nvidia.com/gpu`.
- Requires backend code changes (swap the in-process embedder for an HTTP client),
  so it is intentionally out of scope for this initial manifest PR.

## Notes

- These manifests are a development baseline (single-replica stateful services). A
  production setup would add managed/replicated storage, real secrets management,
  TLS on the Ingress, and resource tuning.
