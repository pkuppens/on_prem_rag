# dbt (Data Build Tool)

Created: 2026-10-29
Updated: 2026-10-29

## What and why

[dbt](https://docs.getdbt.com/) turns SQL `select` statements into tested, documented, versioned tables and views.
It is here to replace hand-rolled Python transformations (WBSO commit/event normalization, session dedup,
`Counter`-based reporting) with declarative SQL models, and to give ingestion/evaluation metadata a lineage graph.
Roadmap: epic [#190](https://github.com/pkuppens/on_prem_rag/issues/190).

The adapter is [dbt-duckdb](https://github.com/duckdb/dbt-duckdb): an in-process database in a single file,
so there is no server to run.

## Layout

```
analytics/dbt/
├── dbt_project.yml        # project config (name, paths, materializations)
├── profiles.yml           # connection: DuckDB file analytics/dbt/dev.duckdb (gitignored)
└── models/
    └── staging/           # stg_* models: one per source, rename/cast only
```

`profiles.yml` is committed because it holds no secrets. Set `DBT_DUCKDB_PATH` to put the database elsewhere.

## Run locally

dbt-core and dbt-duckdb are dev dependencies, so `uv sync --group dev` installs them. Run from the project directory
(dbt picks up `profiles.yml` from the current directory):

```bash
cd analytics/dbt
uv run dbt debug    # validate project config + DuckDB connection
uv run dbt run      # build models into dev.duckdb
uv run dbt test     # run data tests
uv run dbt build    # run + test in dependency order
```

Inspect results with the DuckDB Python API, e.g.
`uv run python -c "import duckdb; print(duckdb.connect('dev.duckdb').sql('select * from stg_example'))"`.
