# tests/test_cuda_check.py
"""Tests for the CUDA availability diagnostic.

As a developer, I want a clear CUDA diagnostic with a reliable exit code,
so that I can tell quickly whether my GPU setup works.
Technical: torch is replaced by a fake module so no GPU or torch build is needed.
"""

import sys
from types import SimpleNamespace

import pytest

from backend.rag_pipeline.utils import cuda_check


def make_fake_torch(*, version="2.6.0+cu126", cuda_available=True, tensor_error=None):
    """Build a stand-in for the ``torch`` module with just the attributes cuda_check reads."""

    def zeros(*_args, **_kwargs):
        if tensor_error:
            raise RuntimeError(tensor_error)

    props = SimpleNamespace(name="Fake GPU", total_memory=8 * 1024**3)
    return SimpleNamespace(
        __version__=version,
        zeros=zeros,
        version=SimpleNamespace(cuda="12.6"),
        backends=SimpleNamespace(cudnn=SimpleNamespace(version=lambda: 9000)),
        cuda=SimpleNamespace(
            is_available=lambda: cuda_available,
            device_count=lambda: 1,
            get_device_properties=lambda _i: props,
        ),
    )


def test_check_torch_exits_1_when_torch_is_missing(monkeypatch, capsys):
    """Missing torch should print an install hint and exit with code 1."""
    monkeypatch.setitem(sys.modules, "torch", None)  # makes `import torch` raise ImportError

    with pytest.raises(SystemExit) as exc:
        cuda_check._check_torch()

    assert exc.value.code == 1
    assert "not installed" in capsys.readouterr().out


def test_check_torch_exits_1_and_prints_help_for_cpu_build(monkeypatch, capsys):
    """A CPU-only torch build should explain how to get the CUDA build and exit 1."""
    monkeypatch.setitem(sys.modules, "torch", make_fake_torch(version="2.6.0+cpu"))

    with pytest.raises(SystemExit) as exc:
        cuda_check._check_torch()

    out = capsys.readouterr().out
    assert exc.value.code == 1
    assert "CPU build" in out
    assert "nvidia-smi" in out


def test_check_torch_returns_normally_for_cuda_build(monkeypatch, capsys):
    """A CUDA build of torch passes the build check without exiting."""
    monkeypatch.setitem(sys.modules, "torch", make_fake_torch())

    cuda_check._check_torch()

    assert "(CUDA build)" in capsys.readouterr().out


def test_check_cuda_available_returns_false_without_gpu(monkeypatch, capsys):
    """No visible GPU: report 'No', print troubleshooting and return False."""
    monkeypatch.setitem(sys.modules, "torch", make_fake_torch(cuda_available=False))

    assert cuda_check._check_cuda_available() is False

    out = capsys.readouterr().out
    assert "CUDA available: No" in out
    assert "Troubleshooting" in out


def test_check_cuda_available_returns_true_and_lists_gpus(monkeypatch, capsys):
    """Working GPU: list device details and return True after the tensor sanity check."""
    monkeypatch.setitem(sys.modules, "torch", make_fake_torch())

    assert cuda_check._check_cuda_available() is True

    out = capsys.readouterr().out
    assert "GPU 0: Fake GPU (8.00 GB)" in out
    assert "tensor creation on GPU OK" in out


def test_check_cuda_available_returns_false_when_tensor_creation_fails(monkeypatch, capsys):
    """Driver/runtime problems surface as a failed sanity check, not an exception."""
    monkeypatch.setitem(sys.modules, "torch", make_fake_torch(tensor_error="out of memory"))

    assert cuda_check._check_cuda_available() is False

    assert "Sanity check FAILED: out of memory" in capsys.readouterr().out


@pytest.mark.parametrize(("cuda_available", "expected_exit_code"), [(True, 0), (False, 1)], ids=["cuda-ok", "no-cuda"])
def test_main_exit_code_reflects_cuda_availability(monkeypatch, cuda_available, expected_exit_code):
    """main() should exit 0 only when CUDA works, so scripts can branch on it."""
    monkeypatch.setitem(sys.modules, "torch", make_fake_torch(cuda_available=cuda_available))

    with pytest.raises(SystemExit) as exc:
        cuda_check.main()

    assert exc.value.code == expected_exit_code
