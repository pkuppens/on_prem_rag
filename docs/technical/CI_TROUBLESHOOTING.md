# CI Troubleshooting: Unit Test Failures

## Summary: "Fatal Python error: Illegal instruction"

**Symptom:** Unit tests fail on GitHub Actions with `Fatal Python error: Illegal instruction` during fixture setup. Tests pass locally.

**Root cause:** CPU instruction set mismatch. PyTorch (and related native libs like FBGEMM) are compiled with AVX2/AVX-512 optimizations. Some GitHub-hosted Ubuntu runners use older CPUs that do not support these instructions. When a test loads `nemoguardrails` or `GuardrailsManager` (which imports transformers/torch), the process crashes.

**Affected tests:** Any test that loads the `GuardrailsManager` fixture or triggers nemoguardrails/torch import, including:
- `tests/backend/guardrails/test_guardrails_manager.py`
- Other tests that indirectly load PyTorch during fixture setup

**Workers crash non-deterministically** because pytest-xdist schedules tests across workers; the first worker to load torch in a given run hits the illegal instruction.

## Answers to Common Questions

### 1. Do the tests fail locally?

**No.** Unit and integration tests pass locally. The failure is specific to GitHub Actions runners (Ubuntu on x86_64 with varying CPU generations).

### 2. Should these be excluded from integration tests?

The failures occur in the **unit test** job, not integration tests. Integration tests pass on GitHub. The guardrails tests are unit tests (no `internet` marker). Excluding them from unit tests would reduce coverage; the preferred fix is to address the setup.

### 3. Is it a GitHub setup issue?

**Yes.** It is a known compatibility issue between PyTorch CPU binaries and older CPUs on hosted runners. See:
- [PyTorch #13993](https://github.com/pytorch/pytorch/issues/13993) (FBGEMM AVX2)
- [PyTorch #37786](https://github.com/pytorch/pytorch/issues/37786) (CPU capability testing)

## Mitigation Options

1. **Environment variables** (add to unit test step): `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1` – may reduce crashes in some BLAS paths.
2. **Disable pytest-xdist** for unit tests (`-n 0`) – avoids worker processes; may still crash when torch loads in main process.

## Parallel Unit Tests (Issue #118)

CI uses `-n 2 --dist loadfile` for unit tests (GitHub runners are 2-core). pytest-cov auto-combines coverage from workers. SQLite in memory tests: `init_memory_database()` handles "table already exists" races; `--dist loadfile` keeps tests from the same file on one worker, reducing DB contention.
3. **Skip guardrails tests on CI** – pragmatic workaround: mark affected tests with `@pytest.mark.skipif(os.environ.get("CI"), reason="PyTorch CPU compatibility on GitHub runners")`.
4. **PyTorch CPU-only wheel** – use `--extra-index-url https://download.pytorch.org/whl/cpu` for a potentially more compatible build (needs evaluation).
5. **Larger runners** – GitHub’s larger hosted runners may use newer CPUs, but with higher cost.

## Current Workaround

The workflow excludes guardrails manager tests on CI via `-m "not guardrails_ci_skip"`. These tests are marked with `@pytest.mark.guardrails_ci_skip` because they load PyTorch/nemoguardrails and trigger "Illegal instruction" on some GitHub runner CPUs.

**To run guardrails tests locally:**
```bash
uv run pytest tests/backend/guardrails/test_guardrails_manager.py -v
# Or run all tests including guardrails:
uv run pytest -m "not internet and not slow" -v
```

The unit test step also sets `OMP_NUM_THREADS=1` and `OPENBLAS_NUM_THREADS=1` as a secondary mitigation.

## ci_skip: Tests Requiring CI-Unavailable Resources

**Symptom:** Tests pass locally but fail on GitHub Actions because required models (e.g. cross-encoder) are not pre-downloaded, or runners lack sufficient resources.

**Affected tests:** `tests/test_retrieval_strategies.py::TestCrossEncoderReranker::test_reranker_returns_top_k` — requires `cross-encoder/ms-marco-MiniLM-L-6-v2`, which is not in the CI HuggingFace cache (setup_embedding_models.py --ci only downloads embedding models).

**Workaround:** Tests are marked `@pytest.mark.ci_skip`. CI excludes them via `-m "not ci_skip"`.

**To run ci_skip tests locally:**
```bash
uv run pytest tests/test_retrieval_strategies.py -m "slow" -v
```

## PDF Chunk Count Change (Character vs Token Chunking)

**Symptom:** `test_pdf_embedding_integration.py` fails with `assert 1895 == 603` on chunk count.

**Root cause:** Issue #79 switched to character-based chunking (512 chars, 25 overlap). Token-based chunking produced ~603 chunks for the test PDF; character-based produces ~1895. Tests that hardcode the old count fail.

**Fix:** Update `EXPECTED_CHUNKS` in the test to match the current chunking strategy (1895 for character-based), or make assertions use the actual chunk count from the result (e.g. `embedding_data["chunks"]` instead of a constant).
