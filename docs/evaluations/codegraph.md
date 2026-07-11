# Evaluation: CodeGraph for AI-assisted codebase navigation

**Tested version:** CodeGraph CLI v1.4.1 (`@colbymchenry/codegraph` on npm)
**Date:** 2026-07-11
**Related issue:** [#176](https://github.com/pkuppens/on_prem_rag/issues/176)
**Tested against:** this repo (`on_prem_rag`), 532 indexed files
**Tested coding agent:** Claude Code (CLI equivalents used for MCP-tool output — see [Limitations](#limitations-of-this-evaluation))

## Recommendation: **Optional**

Document CodeGraph as an optional tool for large refactoring, impact-analysis, and unfamiliar-code
exploration tasks — do not make it a required part of the standard workflow. It produced accurate,
useful results in every task tested here and is genuinely local/private, but its installation
footprint is global rather than per-repo, it adds a Node.js CLI dependency to a Python project, and
one real graph-quality gap (symbol-name collisions across this repo's duplicate legacy/current
modules) needs a workaround. See [Decision rationale](#decision-rationale) for the full reasoning.

## Installation and configuration steps

```bash
# 1. Install the CLI (global npm install; no separate Node version pin required)
npm i -g @colbymchenry/codegraph

# 2. Register the MCP server + agent instructions for detected coding agents
#    (auto-detects Claude Code, Cursor, Codex CLI, opencode, Gemini CLI, etc.)
codegraph install -y

# 3. Build the index for this repo (from the repo root)
cd on_prem_rag
codegraph init
```

`codegraph init` creates `.codegraph/codegraph.db` (a local SQLite+FTS5 database). Add it to
`.gitignore` (done in this PR, alongside the existing `.serena/` entry):

```gitignore
# CodeGraph local structural index (see docs/evaluations/codegraph.md)
.codegraph/
```

### Recommended: disable telemetry

Telemetry is on by default. It's documented as anonymous (event counts, durations, language names,
a random machine ID — never source, paths, symbol names, or queries; see
[TELEMETRY.md](https://github.com/colbymchenry/codegraph/blob/main/TELEMETRY.md)), but for an
on-premises/confidential-code project the safer default is to turn it off:

```bash
codegraph telemetry off
# or: export CODEGRAPH_TELEMETRY=0
```

### Scoping the agent install (important)

`codegraph install -y` defaults to `--target=auto`, which configures **every** coding agent it
detects on the machine (Claude Code, Cursor, Codex CLI, opencode, Gemini CLI), not just the one
you're currently using. If you only want Claude Code:

```bash
codegraph install -t claude-code -y
```

To remove an agent's integration later without uninstalling the CLI:

```bash
codegraph uninstall -t cursor,codex,opencode,gemini -y --keep-cli
# or remove everything:
codegraph uninstall -y
```

`codegraph install` also (a) adds a global `UserPromptSubmit` hook (`codegraph prompt-hook`) that
runs on every prompt in every Claude Code session on the machine, (b) merges `mcp__codegraph__*`
into the global auto-allow permission list, and (c) creates/edits a **global**
`~/.claude/CLAUDE.md` instructing the agent to prefer CodeGraph over grep/read when a `.codegraph/`
directory is present. Functionally this is a no-op in repos without `.codegraph/`, but the
installation footprint itself is machine-global, not repo-local — there's no repo-committable
config (e.g. a project `.mcp.json`) that would let a repo "bring its own" CodeGraph config the way
some other MCP tools support.

## Tested AI coding tools

Only **Claude Code** was tested end-to-end (installing/indexing/running comparative tasks).
`codegraph install` also configured Cursor, Codex CLI, opencode, and Gemini CLI on this machine as
a side effect of the default `--target=auto` scope, but none of those were exercised in this
evaluation.

**MCP-tool caveat:** the `codegraph` MCP server is registered globally in `~/.claude.json`, but MCP
servers are only loaded at Claude Code session start. Because the install happened *during* the
Claude Code session used for this evaluation, the live `codegraph_explore`/`codegraph_node` MCP
tools were not discoverable in that same session (confirmed via tool search — no matches). All
task results below therefore used the equivalent **CLI** commands (`codegraph explore`,
`codegraph node`, `codegraph query`, `codegraph callers`, `codegraph callees`, `codegraph impact`,
`codegraph affected`), which the tool's own documentation states produce identical output to the
MCP tools. **A fresh Claude Code session should be started and `codegraph_explore` availability
confirmed manually** before treating MCP integration as fully verified — this is the one
acceptance-criteria item not independently confirmed in this session.

## Representative tasks and results

Five tasks were run, each once via CodeGraph and once via the equivalent plain grep/read workflow,
then every CodeGraph answer was manually spot-checked against the actual source before being
recorded as correct.

| # | Task | CodeGraph calls | Manual-equivalent calls | Correctness after verification |
|---|------|:---:|:---:|---|
| 1 | Identify main application entry points | 1 (`explore`) | 1 (+more for caller/test context) | Correct — found both live `FastAPI()` apps (`query_service`, `auth_service`) |
| 2 | Trace document ingestion flow (load→chunk→embed→store→retrieve→LLM) | 1 (`explore`) | 1 (+2-3 to disambiguate) | Correct, and surfaced a real repo finding (see below) |
| 3 | Find implementations/usages of `VectorStoreManager` ABC | 3 (`callers`/`impact`/`query`) | 1 (+2-3 to rule out false positives) | Correct — more precise than grep |
| 4 | Identify config/env vars for the vector store | 2 (`explore` + follow-up grep) | ~2 | Correct |
| 5 | Impact/affected-tests analysis for the chunking factory | 2 (`impact`/`affected`) | 1 (+2 to resolve ambiguity) | Correct, initially looked wrong until cross-checked |

**Totals:** ~8 CodeGraph calls vs. an estimated ~14-17 manual calls to reach equivalent confidence
across the same 5 tasks, with CodeGraph avoiding two disambiguation traps a naive grep workflow
fell into (see below). No task produced an outright incorrect final answer after verification.

### Notable findings surfaced by the tool itself

- **Duplicate module pair.** This repo has *two* parallel implementations of document loading and
  chunking: a current one under `backend/ingestion/infrastructure/` (part of the DDD bounded-context
  migration referenced in the root `CLAUDE.md`) and a legacy one still present under
  `backend/rag_pipeline/core/`. CodeGraph's call-graph-weighted `explore` surfaced the
  currently-referenced module directly; a plain `grep "document_loader"` returned all 7 hits
  (both modules plus callers) with no signal about which one is live, requiring several more reads
  to figure out manually.
- **Comment-only false positives excluded.** Two of five `grep "VectorStoreManager"` hits
  (`retrieval/infrastructure/vector_store.py`, `bm25_store.py`) were only in code comments
  ("Extracted from ChromaVectorStoreManager…"), not real references. CodeGraph's structural
  `impact`/`callers` correctly excluded both.
- **Real, previously-unnoticed test-coverage gap.** `codegraph affected` reported zero tests cover
  `backend/ingestion/infrastructure/chunking.py`'s `chunk_documents`. This first looked like a false
  negative (some test files do mention a `chunk_documents` function) — but those tests import it
  from the *legacy* `backend.rag_pipeline.core.chunking` module, a different function. CodeGraph was
  right: the current ingestion-context chunking module genuinely has no test coverage. This is a
  legitimate, actionable finding about the codebase, independent of the CodeGraph evaluation.

## Graph-quality limitations

- **Symbol-name collisions across duplicate modules are not disambiguated by name-based CLI
  queries.** Because `_get_chunking_parser`, `_create_character_strategy`, etc. exist identically
  named in both the legacy and current chunking modules, `codegraph callees <name>` returned
  **merged** results from both files with no way to tell them apart without switching to a
  `file:line`-qualified query (`codegraph node`). For a codebase mid-migration with duplicate
  legacy/current module pairs — which is exactly this repo's situation in several bounded
  contexts — this is a real limitation, not just theoretical.
- **Dynamic dispatch via string-keyed factories worked correctly** in the one case tested
  (`_get_chunking_parser`'s strategy-name branch resolving to the right constructor functions) —
  better than grep, which wouldn't connect the string branch to its target without a manual read.
- **FastAPI route detection looks solid**: `codegraph status` reported 64 `route` nodes vs. 60 from
  a manual `grep -rn "@router\.(get|post|delete|put|patch)"` — the small delta is plausibly
  WebSocket routes or multi-line decorators the grep regex missed, not a CodeGraph gap.
- Dependency injection, decorator-based registration beyond FastAPI routes, and cross-language
  (Python↔TypeScript) linkage were not deeply tested in this pass — flagged as open items for a
  future deeper look if this tool is escalated from "optional" to "adopt."

## Security and privacy findings

- **Fully local indexing**, confirmed by inspecting `.codegraph/codegraph.db` directly: the `nodes`
  table stores structural metadata only (`name`, `qualified_name`, `file_path`, `signature`,
  `docstring`, `decorators`, line ranges) — **no full source-body column**. `codegraph
  explore`/`node` re-read source from disk live at call time rather than serving a cached copy,
  per the tool's own output framing.
- **No secrets found** in a scan of every `docstring`/`signature` value in the index for
  API-key-shaped strings, AWS access key IDs, PEM private-key headers, and inline
  `password = "..."` literals.
- **Exclusions verified**: `.venv`, `node_modules`, `data/`, `chroma_db/`, `.env`, and the Google
  Calendar credential files (`docs/project/hours/scripts/credentials.json`, `token.json`) are all
  excluded from the index — spot-checked via `codegraph query`/`codegraph files`, matching this
  repo's `.gitignore`.
- **Telemetry** is on by default and, per the vendor's published policy, sends only anonymous
  counts/durations/language names/machine ID to a first-party endpoint — never source, paths,
  symbol names, or queries. This was taken on the documented policy, not independently verified via
  packet capture. **Disabled it** (`codegraph telemetry off`) as the recommended default for this
  project regardless.
- **MCP server scope**: `codegraph serve --mcp` runs as a per-session stdio process launched by the
  calling agent in its own working directory. No evidence was found of it serving multiple projects
  from a single process, but this was not independently verified by reading the CodeGraph source
  (a closed npm package, not vendored into this repo) — noted as an assumption.

## Maintenance impact

- **Indexing speed**: 532 files → 6,613 nodes / 15,127 edges / 19 MB DB in **1.4s** of actual parse
  time (7.3s wall-clock including CLI/Node startup overhead).
- **Incremental sync**: a 1-file edit synced in **219ms**. Cheap enough to run on every save if
  wired to a file-watcher daemon (`codegraph daemon`), though the always-on daemon itself wasn't
  exercised in this evaluation — only manual `codegraph sync`.
- **Per-developer setup**: every developer who wants CodeGraph must run `npm i -g
  @colbymchenry/codegraph` + `codegraph init` locally — there's no way to commit a pre-built
  `.codegraph/codegraph.db` (nor would you want to: it would go stale and bloat the repo by
  ~20 MB per snapshot). This mirrors the existing `.serena/` per-developer setup already accepted
  in this repo.
- **Global vs. per-repo config**: `codegraph install` only needs to run once per developer
  machine (not per repo), but it edits global agent config rather than anything repo-committable —
  see the [Scoping the agent install](#scoping-the-agent-install-important) section above for how
  to limit its blast radius.
- **New dependency class**: this is primarily a `uv`/Python project (per the root `CLAUDE.md`
  toolchain table); CodeGraph adds a global Node.js CLI dependency. `src/frontend` already brings
  Node into the repo for the React app, so this isn't unprecedented, but it's a new *global*
  (machine-wide, not repo-scoped) Node dependency for anyone using CodeGraph, independent of
  whether they ever touch the frontend.

## Recommended project instructions or skills

Not added in this PR, consistent with the "Optional" recommendation — no default project
instruction should assume CodeGraph is present. If a developer opts in locally, `codegraph install`
already creates a global `~/.claude/CLAUDE.md` snippet that self-gates on `.codegraph/` existing, so
no repo-level `CLAUDE.md` change is needed for personal opt-in use. If this evaluation is revisited
and upgraded to "Adopt," the natural next step would be a project-level `.mcp.json` (once/if
CodeGraph supports repo-scoped config) plus a short mention in the root `CLAUDE.md` "Workspace
Commands" table.

## Decision rationale

Weighed against the issue's decision criteria:

**For adoption:** results were correct in all 5 representative tasks after verification; it
noticeably reduced the number of tool calls and avoided two disambiguation traps (duplicate module
names, comment-only string matches) a plain-grep workflow fell into; it surfaced one genuine,
previously-unnoticed test-coverage gap in the codebase; it stayed fully local with no secrets in the
index and a documented, disableable telemetry policy; incremental sync is fast (219ms/file).

**Against unconditional adoption:** the installation footprint is global (agent configs, hooks,
CLAUDE.md across every detected agent) rather than repo-scoped, which doesn't fit a workflow that
wants every contributor to get identical, git-committed tooling with zero manual global setup; it
adds a global Node.js CLI dependency purely for Python-repo exploration; one real graph-quality gap
was found (symbol-name collisions across this repo's several duplicate legacy/current module pairs,
which is a recurring pattern here, not a one-off); and live MCP-tool integration in an active Claude
Code session was not independently confirmed (only the CLI-equivalent commands were exercised).

None of these are severe enough to reject the tool outright — but they're enough friction and
unverified surface area that it shouldn't be a required part of this project's workflow yet.
**Optional** — worth using for large refactors or unfamiliar-territory exploration on a per-developer,
opt-in basis; revisit for "Adopt" once (a) a fresh-session MCP tool call has been manually confirmed,
and (b) the symbol-collision behavior across this repo's remaining legacy/current module pairs has
been checked against a few more real edits.

## Limitations of this evaluation

- MCP-tool-in-live-session behavior was proxied via CLI commands documented to produce identical
  output, not exercised through an actual fresh-session MCP tool call (see caveat above).
- Only Claude Code was exercised end-to-end; Cursor/Codex CLI/opencode/Gemini CLI were configured
  by `codegraph install`'s default scope but not tested.
- Telemetry's "anonymous, no source/paths/queries" claim was verified against the vendor's published
  `TELEMETRY.md`, not independently confirmed via network capture.
- Dependency injection, non-FastAPI decorator registration, and cross-language (Python↔TypeScript)
  linkage were only lightly touched, not deeply tested.

A full narrative session transcript (commands run, raw output, and the reasoning behind each
decision made during this investigation, including the scope-overreach flag on the global agent
install) was posted incrementally as comments on
[issue #176](https://github.com/pkuppens/on_prem_rag/issues/176) as the investigation proceeded.
