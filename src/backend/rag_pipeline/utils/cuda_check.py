"""Report and troubleshoot PyTorch CUDA availability for local development.

This module checks whether PyTorch is installed with CUDA/GPU support and
reports diagnostic information. Use it locally to verify GPU setup (e.g.
RTX 4090). GitHub Actions and CI typically run CPU-only; that is expected.

Exit codes:
    0: CUDA is available and working.
    1: CUDA not available (CPU build, no GPU, or driver/runtime issues).

Run via: uv run is-cuda-available
"""

from __future__ import annotations

import sys


def _check_torch() -> None:
    """Check if torch is installed and gather version info."""
    try:
        import torch
    except ImportError:
        print("ERROR: PyTorch (torch) is not installed.")
        print("       Run: uv sync --group dev")
        sys.exit(1)

    build = "CPU" if "+cpu" in torch.__version__ else "CUDA"
    print(f"PyTorch version: {torch.__version__} ({build} build)")

    if build == "CPU":
        _print_cpu_build_troubleshooting()
        sys.exit(1)


def _print_cpu_build_troubleshooting() -> None:
    """Print steps to install CUDA-backed PyTorch for local development."""
    print("\n--- PyTorch is using the CPU build (expected in CI, not ideal locally) ---")
    print("\nTo get CUDA support on a machine with an NVIDIA GPU (e.g. RTX 4090):")
    print("\n1. Ensure NVIDIA driver supports your GPU and CUDA.")
    print("   Check: nvidia-smi")
    print("\n2. Replace the CPU torch with the CUDA build:")
    print("   uv pip install torch --index-url https://download.pytorch.org/whl/cu126")
    print("   (Use cu124 if CUDA 12.4 is preferred; cu126 recommended for RTX 4090)")
    print("\n3. Re-run to verify (use --no-sync so uv does not overwrite with CPU):")
    print("   uv run --no-sync is-cuda-available")
    print("\nSee docs/technical/CUDA_SETUP.md for full setup guide.")


def _check_cuda_available() -> bool:
    """Check if CUDA is available and report GPU details."""
    import torch

    if not torch.cuda.is_available():
        print("\nCUDA available: No")
        _print_generic_troubleshooting()
        return False

    print("\nCUDA available: Yes")
    print(f"CUDA version (PyTorch build): {torch.version.cuda or 'N/A'}")
    print(f"cuDNN version: {torch.backends.cudnn.version()}")
    print(f"Device count: {torch.cuda.device_count()}")

    for i in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(i)
        mem_gb = props.total_memory / (1024**3)
        print(f"  GPU {i}: {props.name} ({mem_gb:.2f} GB)")

    # Quick sanity check: create a small tensor on GPU
    try:
        _ = torch.zeros(1, device="cuda")
        print("\nSanity check: tensor creation on GPU OK")
    except RuntimeError as e:
        print(f"\nSanity check FAILED: {e}")
        _print_generic_troubleshooting()
        return False

    return True


def _print_generic_troubleshooting() -> None:
    """Print generic CUDA troubleshooting steps."""
    print("\n--- Troubleshooting ---")
    print("• Run 'nvidia-smi' to verify the driver sees your GPU.")
    print("• Ensure you installed the CUDA build: uv pip install torch --index-url https://download.pytorch.org/whl/cu126")
    print("• Python 3.12/3.13 is supported by PyTorch 2.6+ with CUDA.")
    print("• See docs/technical/CUDA_SETUP.md for details.")


def main() -> None:
    """Run the CUDA availability check and exit with appropriate code."""
    print("=== PyTorch CUDA Availability Check ===\n")
    _check_torch()

    print(f"Python: {sys.version.split()[0]}")

    cuda_ok = _check_cuda_available()
    sys.exit(0 if cuda_ok else 1)


if __name__ == "__main__":
    main()
