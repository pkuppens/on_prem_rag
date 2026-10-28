# Local CUDA Setup for PyTorch and Whisper

Created: 2026-02-12
Updated: 2026-10-28

This guide describes how to enable CUDA/GPU support for PyTorch on local development machines (e.g. RTX 4090). CI and GitHub Actions run CPU-only by design.

## Python Version

**Python 3.12 and 3.13** are fully supported by PyTorch 2.6+ with CUDA. No need to downgrade. The project `requires-python = ">=3.12,<3.14"` is compatible.

## How torch is installed

`uv sync` installs the right build per platform (see `[tool.uv.sources]` in `pyproject.toml`, #212):

- **Windows**: `torch==2.10.0+cu126` from the PyTorch CUDA 12.6 index. PyPI only has CPU wheels for Windows.
- **Linux (CI)**: `torch==2.10.0` from PyPI, which ships CUDA support on Linux. CI runners have no GPU, so `torch.cuda.is_available()` is False there.

No manual `uv pip install` and no `UV_NO_SYNC` are needed. A plain `uv sync`, including the one the pre-push hook runs, keeps the CUDA build.

## Setup Steps (Local Development)

1. Verify the NVIDIA driver sees the GPU and supports CUDA 12.6+: `nvidia-smi`
2. Install dependencies: `uv sync --group dev` (the first sync downloads the ~2.5 GB CUDA wheel)
3. Verify: `uv run is-cuda-available` (exit code 0 means CUDA is working)

If you set `UV_NO_SYNC=1` for the old manual setup, remove it. It is no longer needed, and it stops `uv run` from applying lockfile updates.

## CI and GitHub Actions

GitHub Actions runners have no GPU. CI uses PyPI torch on Linux and is unaffected by the Windows CUDA index.

## faster-whisper and CTranslate2

The `faster-whisper` package uses CTranslate2 for inference. For GPU-accelerated transcription:

- CTranslate2 needs the CUDA 12 cuBLAS and cuDNN 9 DLLs. On Windows, the CUDA torch wheel bundles them in `torch/lib`, so no separate CUDA toolkit install is needed.
- Without them, transcription on `cuda` fails with `Library cublas64_12.dll is not found or cannot be loaded`.
- See [faster-whisper](https://github.com/SYSTRAN/faster-whisper) docs for GPU setup.

## Speech-to-Text (STT) with CUDA

The STT transcriber (`backend.stt.transcriber`) uses faster-whisper. Once `uv sync` has installed the CUDA build (see above):

1. **Auto-detect**: If `STT_DEVICE` is unset, the transcriber auto-detects CUDA via `torch.cuda.is_available()` and uses `cuda` when available.
2. **Explicit device**: Set `STT_DEVICE=cuda` in `.env` to force GPU (or `STT_DEVICE=cpu` for CPU-only).
3. **Model**: Set `STT_MODEL_SIZE=turbo` for the large-v3-turbo model (good speed/accuracy for multilingual).
4. **Compute type**: When using `cuda`, the default is `float16`. Override with `STT_COMPUTE_TYPE=float16` or `int8` if needed.

Environment variables (see `env.example`):

| Variable          | Default (when unset) | Notes                                  |
|-------------------|----------------------|----------------------------------------|
| `STT_DEVICE`      | Auto-detect (cuda if available, else cpu) | `cpu` or `cuda`                  |
| `STT_MODEL_SIZE`  | `small`              | `tiny`, `base`, `small`, `medium`, `turbo`, etc. |
| `STT_COMPUTE_TYPE`| `float16` (cuda) / `int8` (cpu) | `int8`, `float16`, `float32`  |

Verify: `GET /api/v1/speech/info` returns `transcriber.device` (`cpu` or `cuda`), `model_size`, and `compute_type`.

## Reinstalling After Adding CUDA

If you get file lock errors (`cannot access the file because it is being used`) when running `uv sync`, close any running backend or other processes that use the venv, then run `uv sync` again.

## Troubleshooting

| Issue | Check |
|-------|-------|
| `torch.cuda.is_available()` is False | Run `uv run is-cuda-available` for tailored hints |
| CPU build detected on Windows | Run `uv sync --group dev`; check `[tool.uv.sources]` in `pyproject.toml` still maps torch to `pytorch-cu126` |
| Driver not found | Update NVIDIA driver; run `nvidia-smi` |
| Wrong CUDA version | Match driver CUDA to wheel (e.g. cu126 needs CUDA 12.6) |
| `cublas64_12.dll is not found` (STT) | torch is the CPU build: run `uv sync --group dev`, or set `STT_DEVICE=cpu` |

## References

- [PyTorch Get Started](https://pytorch.org/get-started/locally/)
- [PyTorch RELEASE.md](https://github.com/pytorch/pytorch/blob/main/RELEASE.md) – Python/CUDA compatibility matrix
