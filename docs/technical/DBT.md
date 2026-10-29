# dbt (data build tool)

Created: 2026-10-29
Updated: 2026-10-29

## 1. What dbt is

[dbt](https://docs.getdbt.com/) is a command-line tool for the **T** in ELT (Extract, Load, **Transform**).
Data is already loaded into a database; dbt turns it into clean, tested, documented tables and views,
using nothing but SQL `select` statements plus a little YAML.

What dbt adds on top of plain SQL scripts:

| Without dbt | With dbt |
|-------------|----------|
| Scripts full of `create table ... as select` that must run in the right order | Write only the `select`; dbt creates the table/view and works out the build order |
| Data checks scattered in Python, or missing | Tests declared next to the model (`not_null`, `unique`, ...) and run with one command |
| Documentation in a separate wiki that drifts | Descriptions live next to the code; `dbt docs` builds a browsable site with a lineage graph |
| Copy-pasted SQL snippets | Reusable macros (Jinja templates) |

dbt does not move data between systems and does not run a server. It compiles your SQL and sends it to a
database, here [DuckDB](https://duckdb.org/): an in-process database stored in a single file, so no
infrastructure is needed.

### Core concepts

| Concept | What it is | Where it lives |
|---------|------------|----------------|
| **Model** | One `select` statement in a `.sql` file. Becomes a view or table named after the file | `models/` |
| **Seed** | A small CSV file that `dbt seed` loads as a table. For lookup lists and demo data, not bulk data | `seeds/` |
| **Source** | A table that something *outside* dbt loaded (e.g. pipeline output). Declared in YAML, read with `{{ source(...) }}` | `models/**.yml` |
| **ref** | `{{ ref('name') }}` reads another model or seed *and* records the dependency. This is how dbt knows the build order | inside models |
| **Test** | A query that selects rows breaking a rule; zero rows = pass. *Generic* tests are declared in YAML, *singular* tests are `.sql` files | `models/**.yml`, `tests/` |
| **Materialization** | How a model is stored: `view` (saved query), `table` (data copied), `incremental` (only new rows added) | `dbt_project.yml` or model config |
| **Macro** | A reusable Jinja/SQL function | `macros/` |
| **Profile** | Connection settings: which database to build into | `profiles.yml` |

## 2. Walkthrough: from a CSV file to a tested, documented view

The project ships one end-to-end demo. Follow the data:

```
seeds/example_hours_raw.csv            raw CSV, messy category spelling (" research ", "DEVELOPMENT")
        │  dbt seed
        ▼
table  example_hours_raw               loaded as-is, column types set in dbt_project.yml
        │  models/staging/stg_example_hours.sql   select ... lower(trim(category)) ... from {{ ref('example_hours_raw') }}
        ▼
view   stg_example_hours               clean categories
        │  dbt test
        ▼
tests  not_null, accepted_values       declared in models/staging/_staging.yml
       assert_hours_in_valid_range     tests/assert_hours_in_valid_range.sql (0 < hours <= 24)
```

Each file has inline comments explaining its part. Read them in this order:
[`dbt_project.yml`](../../analytics/dbt/dbt_project.yml),
[`seeds/example_hours_raw.csv`](../../analytics/dbt/seeds/example_hours_raw.csv),
[`models/staging/stg_example_hours.sql`](../../analytics/dbt/models/staging/stg_example_hours.sql),
[`models/staging/_staging.yml`](../../analytics/dbt/models/staging/_staging.yml),
[`tests/assert_hours_in_valid_range.sql`](../../analytics/dbt/tests/assert_hours_in_valid_range.sql).

### Run it

dbt-core and dbt-duckdb are dev dependencies, so `uv sync --group dev` installs them. Run dbt from the
project directory, where it picks up `profiles.yml`:

```bash
cd analytics/dbt
uv run dbt debug    # check the config and the DuckDB connection
uv run dbt build    # seed + run + test, in dependency order
```

Expected: `Done. PASS=7 WARN=0 ERROR=0` (1 seed, 1 model, 5 tests).

Look at the result:

```bash
uv run python -c "import duckdb; print(duckdb.connect('dev.duckdb').sql('select * from stg_example_hours'))"
```

### See a test catch bad data

Append a broken row to the CSV and build again:

```bash
echo "2025-09-03,Meetings,25,break it" >> seeds/example_hours_raw.csv
uv run dbt build    # FAIL accepted_values (unknown category) and FAIL assert_hours_in_valid_range (25 hours)
git checkout seeds/example_hours_raw.csv && uv run dbt build   # restore
```

### Browse the docs and lineage graph

```bash
uv run dbt docs generate   # writes the site to target/
uv run dbt docs serve      # opens it at http://localhost:8080
```

Every description from `_staging.yml` appears there. The lineage graph (bottom-right button) shows
`example_hours_raw → stg_example_hours`.

### Other commands

| Command | Does |
|---------|------|
| `dbt seed` | Load the CSV files in `seeds/` |
| `dbt run` | Build models only |
| `dbt test` | Run tests only |
| `dbt build -s stg_example_hours+` | Build one model and everything downstream of it |
| `dbt source freshness` | Check how recent each source's data is (warns after 7 days for the WBSO sources) |
| `dbt show --inline "select * from {{ source('wbso', 'commits') }}"` | Query a source or model ad hoc |
| `dbt clean` | Delete the generated `target/` and `dbt_packages/` |

## 3. Project layout and what goes in git

```
analytics/dbt/
├── dbt_project.yml     committed   project config: name, paths, materializations
├── profiles.yml        committed   connection: DuckDB file dev.duckdb (no secrets)
├── models/             committed   SQL models + YAML docs/tests
├── seeds/              committed   small CSV files
├── tests/              committed   singular SQL tests
├── macros/             committed   reusable SQL (empty for now)
├── dev.duckdb          gitignored  the database dbt builds into
├── target/             gitignored  compiled SQL, run results, docs site
├── dbt_packages/       gitignored  packages installed by `dbt deps`
└── logs/               gitignored  dbt.log
```

Environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `DBT_DUCKDB_PATH` | `dev.duckdb` | Location of the DuckDB database file |
| `DBT_THREADS` | `2` | Models built in parallel. 2 matches a GitHub Actions runner; DuckDB already parallelises each query internally |

## 4. How dbt will serve this project

The WBSO pipeline (`src/wbso/`) turns git commits, calendar events and system logon/logoff events into
hours per R&D category. Today that is hand-written Python: normalization in several places, session
deduplication with loops, and `Counter`-based reports. Those are exactly the jobs dbt models do, with tests
and lineage as a bonus. The demo above is a miniature of it: raw hours with messy categories, cleaned
and validated.

The planned steps, tracked in epic [#190](https://github.com/pkuppens/on_prem_rag/issues/190):

1. **Sources** (#181, done): `system_events`, `calendar_events` and `commits` in
   [`models/staging/wbso/_wbso__sources.yml`](../../analytics/dbt/models/staging/wbso/_wbso__sources.yml), read in place
   from `docs/project/hours/data/`. The file's header explains which pipeline files became sources and why
   (e.g. the raw `commits/*.csv` files are not parseable, so `commits_processed.json` is used)
2. **Staging** (#182): one `stg_` model per source, replacing the Python normalization
3. **Intermediate** (#183): session deduplication as a SQL window function
4. **Marts** (#184): hours per category/month, replacing the `Counter` reports
5. **Tests in CI** (#185) and **docs/lineage** (#186)

A second track (#187-#189) applies the same pattern to RAG ingestion and embedding-evaluation metadata.
