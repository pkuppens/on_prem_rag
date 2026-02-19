#!/usr/bin/env python3
"""Verify STT and CUDA configuration from .env.

Run: uv run --env-file .env python scripts/verify_stt_cuda.py
Or:  uv run python scripts/verify_stt_cuda.py  (if UV_ENV_FILE points to .env)

Checks:
- PyTorch CUDA availability (required when STT_DEVICE=cuda)
- STT env vars (STT_DEVICE, STT_MODEL_SIZE, STT_COMPUTE_TYPE)
- Transcriber resolves correct device and compute_type
"""

from __future__ import annotations

import os
import sys

# Load .env if present (python-dotenv not required; we document --env-file)
# User should run: uv run --env-file .env python scripts/verify_stt_cuda.py


def main() -> None:
    print("=== STT + CUDA Configuration Check ===\n")
    errors: list[str] = []
    warnings: list[str] = []

    # 1. STT env vars
    stt_device = os.getenv("STT_DEVICE", "")
    stt_model = os.getenv("STT_MODEL_SIZE", "")
    stt_compute = os.getenv("STT_COMPUTE_TYPE", "")
    uv_no_sync = os.getenv("UV_NO_SYNC", "")

    print("STT environment variables:")
    print(f"  STT_DEVICE     = {stt_device or '(unset, will auto-detect)'}")
    print(f"  STT_MODEL_SIZE = {stt_model or '(unset, default: small)'}")
    print(f"  STT_COMPUTE_TYPE = {stt_compute or '(unset, default by device)'}")
    print(f"  UV_NO_SYNC     = {uv_no_sync or '(unset)'}")
    print()

    if not stt_device and not stt_model and not stt_compute:
        warnings.append(
            "All STT_* environment variables are unset. "
            "You should run this script with a valid .env file containing STT_* variables and:\n"
            "  uv run --env-file .env python scripts/verify_stt_cuda.py"
        )

    if stt_device and stt_device.lower() == "cuda":
        if not uv_no_sync:
            warnings.append(
                "STT_DEVICE=cuda but UV_NO_SYNC is unset. "
                "uv run may resync and replace CUDA torch with CPU. "
                "Set UV_NO_SYNC=1 in .env or system env."
            )

        # Check PyTorch
        try:
            import torch
        except ImportError:
            errors.append("torch not installed. Run: uv sync --group dev")
        else:
            if "+cpu" in torch.__version__:
                errors.append(
                    f"STT_DEVICE=cuda but PyTorch is CPU build ({torch.__version__}). "
                    "Install CUDA build: uv pip install torch --index-url "
                    "https://download.pytorch.org/whl/cu126 --force-reinstall"
                )
            elif not torch.cuda.is_available():
                errors.append(
                    "PyTorch has CUDA build but torch.cuda.is_available() is False. "
                    "Run: nvidia-smi"
                )
            else:
                print("PyTorch CUDA: OK")
                print(f"  Version: {torch.__version__}")
                print(f"  Device count: {torch.cuda.device_count()}")

    # 2. Transcriber resolution (lazy - only logs, does not load model)
    print("\nTranscriber resolution (no model load):")
    try:
        from backend.stt.transcriber import _get_default_device, _get_default_compute_type

        device = _get_default_device()
        compute = _get_default_compute_type(device)
        print(f"  Resolved device: {device}")
        print(f"  Resolved compute_type: {compute}")
        if device == "cuda" and compute != "float16":
            warnings.append(
                f"Device is cuda but compute_type is {compute}. "
                "Consider STT_COMPUTE_TYPE=float16 for GPU."
            )
    except Exception as e:
        errors.append(f"Transcriber import failed: {e}")

    # Report
    for w in warnings:
        print(f"\nWARNING: {w}")
    for e in errors:
        print(f"\nERROR: {e}")

    if errors:
        print("\n--- Next steps ---")
        print("1. Fix errors above.")
        if any("PyTorch is CPU build" in str(x) for x in errors):
            print("2. See docs/technical/CUDA_SETUP.md for full CUDA setup.")
        sys.exit(1)

    print("\n[OK] STT + CUDA configuration OK")
    sys.exit(0)


if __name__ == "__main__":
    main()
