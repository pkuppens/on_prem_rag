# Local CUDA Setup for PyTorch and Whisper

Created: 2025-02-12
Updated: 2025-02-12

This guide describes how to enable CUDA/GPU support for PyTorch on local development machines (e.g. RTX 4090). CI and GitHub Actions run CPU-only by design.

## Python Version

**Python 3.12 and 3.13** are fully supported by PyTorch 2.6+ with CUDA. No need to downgrade. The project `requires-python = ">=3.12,<3.14"` is compatible.

## Default vs CUDA Install

- **Default** (`uv sync`): Installs PyTorch from PyPI (CPU build). Used by CI and GitHub Actions.
- **Local CUDA**: After sync, replace torch with the CUDA wheel for GPU acceleration.

## Setup Steps (Local Development)

### 1. Verify NVIDIA Driver

```bash
nvidia-smi
```

Ensure the driver sees your GPU and the CUDA version matches the PyTorch build (see below).

### 2. Install Project Dependencies

```bash
uv sync --group dev
```

### 3. Replace PyTorch with CUDA Build

For **RTX 4090** (Ada Lovelace), use CUDA 12.4 or 12.6:

**Windows (PowerShell):**

```powershell
uv pip install torch --index-url https://download.pytorch.org/whl/cu126
```

**Linux/macOS:**

```bash
uv pip install torch --index-url https://download.pytorch.org/whl/cu126
```

Alternative indexes: `cu124` (CUDA 12.4), `cu128` (CUDA 12.8). Choose based on your driver and PyTorch compatibility.

**Notes**:

- Local-only: not persisted to `pyproject.toml` or `uv.lock`; CI and fresh clones keep the CPU build.
- After CUDA install, `uv run` without `--no-sync` will resync and overwrite with CPU. **You must address this** (see step 5).

### 4. Verify CUDA Availability

**Important**: Use `--no-sync` so `uv run` does not resync and overwrite your CUDA build with the CPU version from the lock file:

```bash
uv run --no-sync is-cuda-available
```

Alternatively: `.venv\Scripts\python.exe -c "from backend.rag_pipeline.utils.cuda_check import main; main()"`

Exit code 0 means CUDA is working. The script reports GPU details and troubleshooting hints if not.

### 5. Keep the CUDA build: set UV_NO_SYNC

After installing the CUDA build, `uv run` will resync from the lock file and overwrite with the CPU build unless you set `UV_NO_SYNC=1`. Two options:

**Option A: System or user environment variable (recommended for a dedicated CUDA dev machine)**

Set `UV_NO_SYNC=1` in your Windows environment variables (System properties → Environment variables → User or System variables). Applies to all uv commands in every terminal. No need to pass flags or load files.

**Option B: .env file**

Add `UV_NO_SYNC=1` to your `.env` (see `env.example`). Note: **`uv run` does not auto-load `.env`**. You must either:

- Pass `--env-file .env` on every `uv run` command, or
- Set `UV_ENV_FILE` to your `.env` path (e.g. in system env) so uv loads it when you run `uv run`.

For project-specific, one-time setup on a CUDA machine, the system/user env var is usually simpler.

## CI and GitHub Actions

GitHub Actions and similar CI runners typically have no GPU. Tests and builds use the default CPU PyTorch from `uv sync`. The CUDA install is local-only (via `uv pip install` into the venv) and is not persisted to `pyproject.toml` or `uv.lock`. CI continues to work without changes.

## faster-whisper and CTranslate2

The `faster-whisper` package uses CTranslate2 for inference. For GPU-accelerated transcription:

- CTranslate2 can use CUDA when available.
- Ensure the PyTorch CUDA build is installed (faster-whisper may use it for model loading).
- See [faster-whisper](https://github.com/SYSTRAN/faster-whisper) docs for GPU setup.

## Reinstalling After Adding CUDA

If you get file lock errors (`cannot access the file because it is being used`) when running `uv sync`, close any running backend or other processes that use the venv, then run `uv sync` again.

## Troubleshooting

| Issue | Check |
|-------|-------|
| `torch.cuda.is_available()` is False | Run `uv run --no-sync is-cuda-available` for tailored hints |
| CPU build detected after CUDA install | Set `UV_NO_SYNC=1` (see section 5); reinstall with `--index-url` from PyTorch CUDA index |
| Driver not found | Update NVIDIA driver; run `nvidia-smi` |
| Wrong CUDA version | Match driver CUDA to wheel (e.g. cu126 needs CUDA 12.6) |

## References

- [PyTorch Get Started](https://pytorch.org/get-started/locally/)
- [PyTorch RELEASE.md](https://github.com/pytorch/pytorch/blob/main/RELEASE.md) – Python/CUDA compatibility matrix
