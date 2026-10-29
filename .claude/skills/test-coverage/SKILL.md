---
name: test-coverage
description: Raise Python test coverage on the fly with meaningful, well-documented tests. Measures coverage, ranks the worst gaps (function coverage first, then branch, then line), and guides a test-first loop with fast feedback. Use when asked to increase coverage, restore a coverage gate, or find untested code.
argument-hint: [target-percent | path-to-focus]
---

# Test Coverage Skill (generic, Python)

Goal: raise coverage by writing **tests that verify behaviour**, never tests that merely execute lines.
Generic for any pytest project; the only bundled tool is `coverage_tool.py` (stdlib only, next to this file).

## Principles

1. **Meaningful tests.** Every test asserts an observable outcome. A test with no assertion on behaviour is coverage theatre; do not write it.
2. **Readable** (Code Complete 2, "Writing Code for Humans"): name = `test_<unit>_<scenario>_<expected result>`; one behaviour per test; Arrange / Act / Assert separated by blank lines; one-line docstring stating the behaviour in plain language; no logic (loops/ifs) in tests; use `pytest.mark.parametrize` for table-like cases with `ids=`.
3. **Mock only what is slow or external** (network, LLM, DB server, filesystem outside `tmp_path`, clock, GPU/model loading). Patch where the name is *used*, not defined. Prefer fakes over deep `MagicMock` chains. Never mock the unit under test.
4. **Order: function → branch → line.** First make sure every function executes at least once (`funcs`), then the error/edge branches (`lines`), then leftover lines.
5. **Tests first, code later.** Do not refactor or rewrite production code until it has at least function-level tests. Characterise current behaviour; if behaviour looks like a bug, pin it with a test marked `xfail(strict=True, reason="BUG: ...")` and report it, do not silently fix.
6. **Red-Green-Refactor** where code changes: (Red) write the failing test, (Green) minimal change, (Refactor) only with tests green. For characterisation tests of existing code, "red" means: temporarily break the code (or assert a wrong value) once to prove the test can fail, then restore.
7. **Clear feedback loops** for human and AI: small batches, re-measure after each batch (`compare`), and make failures self-explanatory (assert messages, parametrize ids, no shared mutable state).

## Deterministic commands

Run from the repo root. `T=.claude/skills/test-coverage/coverage_tool.py` (adapt path if promoted to `~/.claude/skills`).

```bash
python $T run --source src -- -m "not slow" -n 4        # pytest + coverage.json at tmp/analysis/coverage.json
python $T summary --depth 1                             # total + per-package table, worst first
python $T files --top 15                                # files ranked by missed lines
python $T funcs --top 20                                # never-executed functions (step 1: function coverage)
python $T lines path/to/file.py                         # missing line ranges / branches (steps 2-3)
python $T compare tmp/analysis/coverage.before.json     # delta after a batch of tests
python $T gate --min 70                                 # exit 1 if below gate (CI-friendly)
```

Use the same pytest selection as CI (markers, offline env vars) so the number matches CI. Keep the `--json` path outside version control (e.g. `tmp/`).

## Workflow

1. **Baseline.** `run`, copy the JSON to `coverage.before.json`, note the total.
2. **Triage** with `summary` and `files`. Decide per package: *test it*, *delete dead code*, or *omit from measurement* (`[tool.coverage.run] omit`). Omit only generated code, legacy shims scheduled for removal, or entry points with no logic; write the reason next to the entry. Never omit to hit a number silently.
3. **Pick a batch**: the top 1-3 files from `funcs`/`files` that hold real logic. Read the code and any existing tests/fixtures first; reuse conftest fixtures.
4. **Write tests** (principles above). Cover happy path, one edge, one failure per function, then loop `pytest <file> -q` until green.
5. **Re-measure** with `run` on just the touched tests for speed (`-- tests/path -q`), then `compare` against the baseline with the full run before committing.
6. **Commit per batch**, message states the module and the before/after number.
7. **Gate.** When the target is reached, set `--cov-fail-under` to the new baseline (rounded down, a little below to absorb noise) in CI, and keep a warning for the stretch target.
8. **Record lessons** (below) before finishing.

## Pitfalls checklist

- Parallel runs (`pytest-xdist`) + shared on-disk resources (DB, vector store) cause flaky collection and misleading coverage; isolate with `tmp_path`/fixtures.
- Coverage measured under `--cov=<src>` ignores files never imported; use `source=` (not just `--cov` on imported modules) so untouched files show 0%.
- Lines excluded via `exclude_lines = ["pass"]` hide real gaps; review exclusions occasionally.
- Import-time side effects (model downloads, network) must be patched before import; use `monkeypatch`/`patch` on the consumer module.
- Async code: `pytest-asyncio` (`@pytest.mark.asyncio` or auto mode); FastAPI: `TestClient` with `app.dependency_overrides`, not patched internals.
- Do not assert on log text/private attributes unless that *is* the contract.

## Lessons learned

Append dated, one-line lessons here as they are discovered (keep it short; promote durable ones into Principles/Pitfalls).

- 2026-10-29: Rank by *missed statements* (not percentage): a 0% 10-line file matters less than a 40% 800-line file.
