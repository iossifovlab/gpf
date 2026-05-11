# GPF Monorepo — Agent Guide

This file provides guidance to Claude Code when working
with code in this repository.

## Project Overview

GPF (Genotypes and Phenotypes in Families) is a system for
managing large databases of genetic variants and phenotypic
measurements from family collections (e.g., the Simons
Simplex Collection with ~2,600 autism families).

## Environment Setup

`uv` is the primary workflow — used by all four CI test
images (`core/`, `web_api/`, `federation/`,
`rest_client/Dockerfile`) and the production builder
(`web_api/Dockerfile.production`). Conda/Mamba is supported
for local development only; CI does not consume it. See
`README.md` for the conda setup commands.

The `gain` package lives in a separate repository
(<https://github.com/iossifovlab/gain>) and must be
checked out as a sibling. Unlike before, gain is **not**
a path source in `pyproject.toml`; it is consumed as a
wheel built by gain's CI and dropped into `dist/gain/`
(tb-eqh phase-5b — fixes the docker-layer-cache hazard
of `RUN git clone gain ... checkout master`).

```bash
# First-time bootstrap of a local checkout
git clone https://github.com/iossifovlab/gain.git ../gain
cd ../gain
uv build --package gain-core --out-dir ../gpf/dist/gain
cd ../gpf
uv sync --find-links ./dist/gain
```

The root `pyproject.toml` is a virtual coordinator
(`[tool.uv] package = false`); default `uv sync`
installs `gpf-core` + `gpf-web`. Common variants:

```bash
# Everything: all workspace members + every dev group
uv sync --find-links ./dist/gain --all-packages --all-groups

# A single workspace member
uv sync --find-links ./dist/gain --package gpf-federation --group dev
```

The storage backends (`impala_storage/`, `impala2_storage/`,
`gcp_storage/`) are deliberately **not** workspace members
— their heavy backend deps (Hadoop, Google Cloud SDKs)
would otherwise enter the workspace lockfile. Install
standalone:

```bash
uv pip install -e ./impala_storage
```

Run any command in the project's environment without
activation via `uv run` (canonical form — works in any
fresh shell, no activation required):

```bash
uv run pytest -v tests/small/
uv run ruff check --fix .
uv run mypy gpf --exclude core/docs/
```

Manage dependencies via uv (don't edit `pyproject.toml`
deps directly; uv updates the lockfile in step):

```bash
cd core && uv add <dep>                  # runtime dep
cd core && uv add --group dev <dep>      # dev dep
cd core && uv remove <dep>
uv lock --upgrade                        # refresh whole lock
uv lock --upgrade-package <dep>          # refresh one
```

After `git pull`, re-run `uv sync --find-links
./dist/gain`. After `git pull` in `../gain/`, rebuild the
gain wheel first (`uv build --package gain-core --out-dir
../gpf/dist/gain` from `../gain/`) unless you've enabled
the editable-gain override (see README.md → "Editable
gain for local development").

### Production image: wheels-only invariant (tb-qp5)

`web_api/Dockerfile.production` enforces a **wheels-only**
install via `uv pip install --only-binary=:all:
--no-binary=mysqlclient`. Any transitive dep without a
cp312-manylinux_x86_64 wheel fails the build loudly
instead of silently growing source-build residue and
inflating cold-build time. `mysqlclient` is the one
documented exception (no manylinux wheel exists on PyPI;
it builds against `libmariadb-dev` installed in the same
builder stage).

To exempt another dep: add it to the `--no-binary=` list
in `web_api/Dockerfile.production` with a justification
comment alongside the mysqlclient note. Don't drop
`--only-binary=:all:` — the strict default is the whole
point of the invariant.

The four CI test Dockerfiles (`core/`, `web_api/`,
`federation/`, `rest_client/Dockerfile`) intentionally do
**not** set `--only-binary=:all:`. They install workspace
members from path sources via `uv sync`, which requires
hatchling to build the package metadata — strict
wheels-only would fail by design there.

## Commands

### Testing

```bash
# Run a single test file
cd core && uv run pytest -v tests/small/path/to/test_file.py

# Run a test module
cd core && uv run pytest -v tests/small/module/

# Run GPF tests in parallel
cd core && uv run pytest -v -n 10 tests/

# Run GPF Web tests in parallel
cd web_api && uv run pytest -v -n 5 gpf_web/
```

Test markers in `core/pytest.ini`: genotype storage
(`gs_impala`, `gs_impala2`, `gs_inmemory`, `gs_gcp`,
`gs_duckdb`, `gs_duckdb_parquet`, `gs_schema2`,
`gs_parquet` and `no_gs_*` exclusion variants) and GRR
(`grr_rw`, `grr_ro`, `grr_full`, `grr_http`, `grr_tabix`).

All tests run with `PYTHONHASHSEED=0`.

### Linting and Type Checking

```bash
# Ruff linting (fast, primary linter)
uv run ruff check --fix .

# Type checking (slow, 2-5 minutes)
uv run mypy gpf --exclude core/docs/
uv run mypy gpf_web --exclude web_api/docs/ \
    --exclude web_api/conftest.py
```

Config: `ruff.toml` (line-length: 80, target: py310),
`mypy.ini` (strict, Django plugin via django-stubs).

### Pre-commit Hook

```bash
cp pre-commit .git/hooks/
```

The pre-commit hook runs `ruff check` (ignoring FIX
warnings) on staged `.py` files.

### Test Infrastructure (Docker)

Some tests require external services. Start them with:

```bash
docker compose up -d
```

Services defined in `docker-compose.yaml`:
- **MinIO** (ports 9000/9001) — S3-compatible object
  storage for GCP/S3 storage tests; credentials
  `minioadmin/minioadmin`, bucket `test-bucket`
- **Apache httpd** (port 28080) — HTTP fixture server for
  `grr_http` tests; serves
  `core/tests/.test_grr/`

## Architecture

### Dependency Direction

Strict layering (the `gain` package lives in
<https://github.com/iossifovlab/gain>):

```
gain  ←  gpf  ←  gpf_web
```

The `gpf` package must **never** import from `gpf_web`.
`gain` must **never** import from `gpf` or `gpf_web` —
that rule is enforced by pytestarch tests in the gain
repository.

### Package Structure

- **`core/`** — GPF core library: genotype storage,
  studies, pedigrees, pheno, import tools, query API.
  Python package: `gpf`. Depends on `gain`.
- **`web_api/`** — Web application: Django REST API on
  top of GPF. Python package: `gpf_web`. Depends on
  `gpf` and `gain`.
- **`impala_storage/`**, **`impala2_storage/`**,
  **`gcp_storage/`** — optional storage backends
- **`federation/`** — federated query support
- **`rest_client/`** — REST API client library

The `gain` package and its annotator plugins
(`gain_spliceai_annotator`, `gain_vep_annotator`,
`gain_demo_annotator`) live in the separate
[`iossifovlab/gain`](https://github.com/iossifovlab/gain)
repository.

### Plugin System

GPF uses Python entry points for extensibility. Entry
points provided by the external `gain` package
(`gain.genomic_resources.plugins`,
`gain.genomic_resources.implementations`,
`gain.annotation.annotators`) are documented in the gain
repo.

**Defined in `core/pyproject.toml`:**

1. **`gain.genomic_resources.plugins`** —
   GPFInstanceContextProvider (gpf hooks into the gain
   plugin system; the entry point lives here because the
   provider references gpf-core code)
2. **`gain.genomic_resources.implementations`** —
   enrichment backgrounds (gene weights, Samocha)
3. **`gpf.genotype_storage.factories`** — inmemory,
   duckdb (legacy, standard, parquet, S3, S3 parquet),
   parquet
4. **`gpf.import_tools.storages`** — import storage
   backends matching each genotype storage type
   (schema2, inmemory, duckdb variants, parquet)

**Defined in `web_api/pyproject.toml`:**

3. **`console_scripts`** — `wgpf` (web server launcher),
   `wdaemanage` (Django management wrapper)

### GPF Core Submodules (`core/gpf/`)

- **`gpf_instance/`** — `GPFInstance` class: central
  coordinator that wires together all GPF components
  (config, GRR, gene models, genome, annotation, pheno,
  studies, storages)
- **`gpf_instance_plugin/`** — genomic context provider
  plugin for GPFInstance
- **`configuration/`** — config parser + validation
  schemas (GPF instance YAML config)
- **`genotype_storage/`** — factory + registry for
  pluggable storage backends
- **`duckdb_storage/`** — DuckDB genotype storage
  (variants: legacy, standard, parquet, S3, S3 parquet)
- **`parquet_storage/`** — Parquet-based genotype storage
- **`inmemory_storage/`** — in-memory genotype storage
- **`schema2_storage/`** — schema2 import storage
- **`parquet/`** — low-level Parquet schema utilities
- **`variants/`** — variant data structures (family
  variant, summary variant)
- **`variants_loaders/`** — loaders for VCF, DAE, denovo,
  CNV file formats
- **`studies/`** — study and dataset management
- **`pedigrees/`** — family/pedigree handling
- **`person_sets/`** — person set definitions + builders
- **`person_filters/`** — person-level query filters
- **`query_variants/`** — query API + query runners
- **`import_tools/`** — data import pipelines + CLI
- **`pheno/`** — phenotypic data import, storage, and
  browser
- **`pheno_tool/`** — phenotypic analysis tool
- **`enrichment_tool/`** — gene enrichment analysis +
  resource implementations
- **`gene_profile/`** — gene profile DB, generation,
  export, DuckDB conversion
- **`gene_sets/`** — denovo gene sets DB + gene sets DB
- **`genomic_scores/`** — genomic scores registry
- **`common_reports/`** — common report generation
- **`testing/`** — test fixture helpers (import utilities)
- **`tools/`** — CLI tools (ped2ped, draw_pedigree,
  liftover, format converters, validation runner)
- **`utils/`** — shared utilities

### GPF Web Structure (`web_api/gpf_web/`)

The web layer is a Django project. The Django project
package is `web_api/gpf_web/gpf_web/` (settings, urls, wsgi).
Django apps sit at `web_api/gpf_web/<app_name>/`.

**Django apps (INSTALLED_APPS order):**

- **`gpfjs`** — SPA static files + index view
- **`utils`** — OAuth2 authentication, pagination helpers
- **`gene_scores`** — gene scores REST API
- **`gene_sets`** — gene sets REST API
- **`datasets_api`** — dataset listing + permissions
- **`genotype_browser`** — variant query/browse endpoints
- **`enrichment_api`** — enrichment analysis endpoints
- **`measures_api`** — phenotypic measures endpoints
- **`pheno_browser_api`** — phenotype browser endpoints
- **`pheno_tool_api`** — phenotype analysis tool
  endpoints
- **`common_reports_api`** — common report endpoints
- **`users_api`** — user management + auth (defines
  custom `WdaeUser` model via `AUTH_USER_MODEL`)
- **`groups_api`** — group/permission management
- **`query_state_save`** — saved query states
- **`user_queries`** — user query history
- **`gpf_instance`** — `WGPFInstance` singleton (wraps
  `GPFInstance`), extension system, instance endpoints

**Apps used via URL routing but not in INSTALLED_APPS:**

- **`gene_profiles_api`** — gene profile data endpoints
- **`gene_view`** — gene-level view endpoints
- **`genomes_api`** — genome/reference data endpoints
- **`genomic_scores_api`** — genomic scores endpoints
- **`family_api`** — family data endpoints
- **`person_sets_api`** — person set endpoints
- **`sentry`** — Sentry integration endpoints

**Shared modules (not Django apps):**

- **`query_base/`** — `QueryBaseView` base class for all
  variant query endpoints (provides OAuth2 auth +
  dataset permission checks)
- **`studies/`** — `QueryTransformer`,
  `ResponseTransformer`, `WDAEStudy`/`WDAEStudyGroup`
  wrappers

**Key patterns:**
- `QueryBaseView` — base class for variant query
  endpoints (in `query_base/`)
- `StreamingHttpResponse` — used for large result sets
- `WGPFInstance` — web-layer singleton wrapping
  `GPFInstance`
- OAuth2 toolkit for multi-tenant authentication
- Tests live inside each app: `<app>/tests/`

### REST API URL Structure

All endpoints under `/api/v3/`:

| Prefix | App |
|---|---|
| `/api/v3/datasets` | `datasets_api` |
| `/api/v3/genotype_browser` | `genotype_browser` |
| `/api/v3/enrichment` | `enrichment_api` |
| `/api/v3/gene_scores` | `gene_scores` |
| `/api/v3/gene_sets` | `gene_sets` |
| `/api/v3/measures` | `measures_api` |
| `/api/v3/pheno_tool` | `pheno_tool_api` |
| `/api/v3/pheno_browser` | `pheno_browser_api` |
| `/api/v3/common_reports` | `common_reports_api` |
| `/api/v3/genomic_scores` | `genomic_scores_api` |
| `/api/v3/gene_profiles` | `gene_profiles_api` |
| `/api/v3/gene_view` | `gene_view` |
| `/api/v3/genome` | `genomes_api` |
| `/api/v3/families` | `family_api` |
| `/api/v3/person_sets` | `person_sets_api` |
| `/api/v3/query_state` | `query_state_save` |
| `/api/v3/user_queries` | `user_queries` |
| `/api/v3/sentry` | `sentry` |
| `/api/v3/instance` | `gpf_instance` |
| `/api/v3/users/...`, `/api/v3/groups/...` | `users_api`, `groups_api` |
| `/o/` | OAuth2 provider |

### Data Flow

```
REST Request → GPF Web Django App
    → QueryBaseView (OAuth2 auth + dataset permissions)
    → QueryTransformer (request normalization)
    → GPF Core (GPFInstance / study)
        → Genotype Storage (DuckDB / Parquet / Impala)
        → Annotation Engine
        → Genomic Resource Repository
    → ResponseTransformer (result formatting)
  → StreamingHttpResponse
```

### Test Structure

`core` uses a `tests/small/` vs `tests/integration/`
split:
- `tests/small/` — unit/fast tests (default for
  development and CI)
- `tests/integration/` — tests requiring external
  services or longer runtime

`web_api` unit tests live inside each Django app:
`web_api/gpf_web/<app>/tests/`
Integration tests are in `web_api/gpf_web_tests/integration/`.

Key conftest patterns:
- **`grr_scheme` parametrization** — tests tagged with
  `grr_rw`, `grr_full`, `grr_http`, `grr_tabix` markers
  are automatically parametrized across GRR protocols
  (inmemory, file, s3, http). Enable S3/HTTP with
  `--enable-s3-testing` / `--enable-http-testing`.
- **`genotype_storage_factory` parametrization** — tests
  tagged with `gs_*` markers run against the appropriate
  storage backends.

### CLI Tools

CLIs from the external `gain` package (`grr_manage`,
`grr_browse`, `annotate_columns`, `annotate_vcf`,
`annotate_doc`, `annotate_variant_effects`,
`annotate_variant_effects_vcf`) are documented in the
[`iossifovlab/gain`](https://github.com/iossifovlab/gain)
repository.

**core CLIs:**
- `import_tools` / `import_genotypes` — genotype data
  import
- `pheno_import` / `build_pheno_browser` /
  `update_pheno_descriptions` — phenotype tools
- `generate_gene_profile` /
  `convert_gene_profile_to_duckdb` — gene profiles
- `gpf_validation_runner` — instance validation
- `gpf_instance_adjustments` — instance adjustments
- `ped2ped`, `draw_pedigree` — pedigree utilities
- `denovo_liftover`, `dae_liftover`, `cnv_liftover`,
  `vcf_liftover` — liftover tools
- `denovo2vcf`, `dae2vcf`, `vcf2tsv` — format converters
- `simple_study_import` — simplified study import
- `generate_common_report` — common reports
- `generate_denovo_gene_sets` — denovo gene sets
- `enrichment_cache_builder` — enrichment cache

**web_api CLIs:**
- `wgpf` — GPF web server launcher
- `wdaemanage` — Django management command wrapper

## Key Dependencies

- **Python 3.12**, Django 5.2, DRF 3.16
- **DuckDB 1.5** — primary embedded storage
- **dask** — parallel computing
- **pandas 2.2**, **numpy 2.2**, **pyarrow >=18** — data
  analysis
- **pysam 0.23** — SAM/BAM file handling
- **pydantic 2.8** — data validation
- **lark 1.2** — parsing (GRR search grammar)
- **fsspec / s3fs** — filesystem abstraction + S3 access
- **Sentry SDK** — error tracking in production
- Dev: **ruff 0.14**, **mypy 1.15**, **pytest**,
  **pytest-xdist**, **pytestarch**

## Django Settings

Settings files in `web_api/gpf_web/gpf_web/`:

- `default_settings.py` — base settings (all others
  import from here)
- `settings.py` — local development
- `test_settings.py` — pytest
  (`DJANGO_SETTINGS_MODULE`)
- `gunicorn_settings.py` — production gunicorn
- `mypy_settings.py` — mypy django-stubs config
- `eager_settings.py` — eager study loading
- `remote_settings.py` — remote/deployed settings
- `wgpf_settings.py` — wgpf CLI settings
- `silk_settings.py` — Django Silk profiler

