# dbt in on_prem_rag — why, what, and what was left out

Created: 2026-10-30
Updated: 2026-10-30

A 3-minute read for someone judging this repo as a work sample. For commands and setup see
[technical/DBT.md](technical/DBT.md). Epic: [#190](https://github.com/pkuppens/on_prem_rag/issues/190).

## The problem

The WBSO (R&D tax credit) hours pipeline in [`src/wbso/`](../src/wbso/) is hand-written Python: it reads
CSV/JSON exports, deduplicates sessions in loops, maps activities to categories, and rolls hours up for reports.
That works, but:

- **Business logic is duplicated.** The activity → category mapping lives in `wbso_activities.json`, is
  re-derived in `reporting.py`, and the rollups are written twice (`database_reporting.py`, `wbso_report_generator.py`).
  A new category added to one place silently diverges from the others.
- **Correctness is implicit.** Dedup is a "keep first, drop rest" loop; nothing declares that `session_id` is unique
  or that hours are between 0 and 24.
- **No lineage.** Answering "which file does this reported number come from?" meant reading code
  (`WBSO-DATA-FLOW.md` says so itself).

The question the epic answers: can a declarative SQL layer (dbt on DuckDB, no server) reproduce the same numbers
with checks and lineage built in, *without* deleting the Python first? Retiring the Python is deliberately a later decision.

## What was built

| dbt concept | Real problem it solved | Where |
|---|---|---|
| **Sources** with freshness | Pipeline outputs are declared, not guessed; raw commit CSVs can't be parsed (unescaped `\|`, one UTF-16 file), so the processed JSON is the source | [#181](https://github.com/pkuppens/on_prem_rag/issues/181), [`_wbso__sources.yml`](../analytics/dbt/models/staging/wbso/_wbso__sources.yml) |
| **Staging** (rename/cast only) | One typed entry point per source; two date formats parsed once | [`stg_wbso__calendar_events`](../analytics/dbt/models/staging/wbso/stg_wbso__calendar_events.sql), [`stg_wbso__system_events`](../analytics/dbt/models/staging/wbso/stg_wbso__system_events.sql), [`stg_wbso__commits`](../analytics/dbt/models/staging/wbso/stg_wbso__commits.sql) |
| **Intermediate** (window functions) | The dedup loop becomes `row_number()` plus a running `max(ended_at)` for overlaps | [`int_wbso__sessions_deduped`](../analytics/dbt/models/intermediate/wbso/int_wbso__sessions_deduped.sql) |
| **Macro** | One activity → category mapping, used by two models | [`normalize_wbso_category`](../analytics/dbt/macros/normalize_wbso_category.sql) |
| **Marts**, **incremental** model | Declarative rollups; the monthly mart reprocesses only the latest month (`delete+insert`) | [`mart_hours_by_category`](../analytics/dbt/models/marts/wbso/mart_hours_by_category.sql), [`mart_hours_by_month`](../analytics/dbt/models/marts/wbso/mart_hours_by_month.sql) |
| **Packages**: `generate_surrogate_key`, `date_spine` | A deterministic key instead of a load-order cache; every month in range shown, zero-filled | [`dim_wbso_categories`](../analytics/dbt/models/marts/wbso/dim_wbso_categories.sql), [`mart_hours_by_month_gapless`](../analytics/dbt/models/marts/wbso/mart_hours_by_month_gapless.sql), [`packages.yml`](../analytics/dbt/packages.yml) |
| **Tests**, incl. a custom generic test | Uniqueness, `accepted_values` on categories, `hours_in_valid_range(min, max)`, and a seed-vs-pipeline drift check | [`hours_in_valid_range`](../analytics/dbt/macros/generic_tests/hours_in_valid_range.sql), [`assert_wbso_repositories_seed_matches_pipeline`](../analytics/dbt/tests/assert_wbso_repositories_seed_matches_pipeline.sql) |
| **Seeds, vars, environments** | Reference list as versioned data; reporting period per run; in-memory `ci` target | [`dbt_project.yml`](../analytics/dbt/dbt_project.yml), [`profiles.yml`](../analytics/dbt/profiles.yml), [#192](https://github.com/pkuppens/on_prem_rag/issues/192) |
| **Exposure**, docs, lineage | The graph ends at the WBSO reports; every model and column has a description | [`exposures.yml`](../analytics/dbt/models/exposures.yml) |
| **CI** | `dbt build` on every change under `analytics/dbt/` or the WBSO data, without the ML dependencies | [`dbt.yml`](../.github/workflows/dbt.yml) |

## Before / after: one mapping, one place

**Before.** Which activity belongs to which WBSO category was encoded separately in `wbso_activities.json` and
`reporting.py`, and the reports aggregated on their own. An unknown activity fell through to a default.

**After.** `normalize_wbso_category(activity_name)` is a dict-driven Jinja macro generated from that JSON, called by
both `int_wbso__sessions_deduped` and `mart_hours_by_category`. Anything unmapped becomes `UNMAPPED`, and an
`accepted_values` test on the category column turns it into a failing build.

**Proof, not claim.** I remapped one activity to a bogus code and rebuilt: `accepted_values` failed with 1 row, then
I reverted. I also added 30 hours to every session: `hours_in_valid_range` failed with all 317 rows. (An earlier attempt
passed by mistake, because I corrupted an activity no session uses and ran `dbt test`, which doesn't rebuild views.
Lesson: negative-test with `dbt build` on data that exercises the rule.)

## Findings about the real data

- The dedup model keeps all **317 of 317** sessions: the data currently has no duplicate ids and no overlaps, so the
  model is a proven no-op on today's data, not evidence that it catches anything on real duplicates.
- Hours match across the chain: **984.45 h** in sessions, the category mart and the zero-filled monthly mart.
- The calendar has no empty month (June–November are all present), so the gapless mart's zero-fill is untested on real data.
- One real session has `hours = 0`, which is why the range test is inclusive of 0.

## Not built, and why

- **Evaluation-run comparison mart** ([#188](https://github.com/pkuppens/on_prem_rag/issues/188)) and **ingestion
  document snapshot** ([#189](https://github.com/pkuppens/on_prem_rag/issues/189)): both need real data (CLI
  evaluation history, a populated `metadata.db`) that isn't in the repo; the issues require real runs, so they stay open.
- The evaluation exposure follows #188; `stg_wbso__system_events` has no mart yet.
- Python code is untouched; deleting it is a follow-up once trust is established.

Out of scope on purpose ([#190](https://github.com/pkuppens/on_prem_rag/issues/190)): **Semantic Layer / MetricFlow**,
**model contracts and versions**, **dbt Mesh** (they solve cross-team interface problems this single-repo project
doesn't have), **Python models** (limited DuckDB support), **dbt Cloud** (dbt-core locally and in GitHub Actions is enough).
