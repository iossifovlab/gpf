# GPF Monorepo — Agent Guide

This file provides guidance to Claude Code when working
with code in this repository.

## Project Overview

GPF (Genotypes and Phenotypes in Families) is a system for
managing large databases of genetic variants and phenotypic
measurements from family collections (e.g., the Simons
Simplex Collection with ~2,600 autism families).

## Environment Setup

**This project supports two workflows: Conda/Mamba and
uv (pyproject-driven, the same workspace pattern as the
gain repo).**

The `gain` package lives in a separate repository
(<https://github.com/iossifovlab/gain>) and must be
checked out as a sibling and installed alongside this
one before the GPF packages will import:

```bash
git clone https://github.com/iossifovlab/gain.git ../gain
```

Conda/Mamba workflow:

```bash
mamba env create --name gpf --file ./environment.yml
mamba env update --name gpf --file ./dev-environment.yml
conda activate gpf

pip install -e ../gain/core
pip install -e core
pip install -e web
```

uv workspace workflow (root `pyproject.toml` is a virtual
coordinator with `[tool.uv] package = false`):

```bash
# Default: gpf-core + gpf-web
uv sync

# Everything: all workspace members + every dev group
uv sync --all-packages --all-groups

# A single sub-project
uv sync --package gpf-impala-storage --group dev
```

## Commands

### Testing

```bash
# Run a single test file
cd core && pytest -v tests/small/path/to/test_file.py

# Run a test module
cd core && pytest -v tests/small/module/

# Run GPF tests in parallel
cd core && pytest -v -n 10 tests/

# Run GPF Web tests in parallel
cd web && pytest -v -n 5 gpf_web/
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
ruff check --fix .

# Type checking (slow, 2-5 minutes)
mypy gpf --exclude core/docs/
mypy gpf_web --exclude web/docs/ \
    --exclude web/conftest.py
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

### Do NOT run locally

`build.sh` requires Docker and a private `build-scripts`
submodule — it's only for CI (Jenkins).

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
- **`web/`** — Web application: Django REST API on
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

**Defined in `web/pyproject.toml`:**

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

### GPF Web Structure (`web/gpf_web/`)

The web layer is a Django project. The Django project
package is `web/gpf_web/gpf_web/` (settings, urls, wsgi).
Django apps sit at `web/gpf_web/<app_name>/`.

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

`web` unit tests live inside each Django app:
`web/gpf_web/<app>/tests/`
Integration tests are in `web/gpf_web_tests/integration/`.

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

**web CLIs:**
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

Settings files in `web/gpf_web/gpf_web/`:

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

<!-- BEGIN BEADS INTEGRATION v:2 profile:minimal -->
## Beads Issue Tracker

This project uses **br (beads_rust)** for issue tracking.

**Note:** `br` is non-invasive and never executes git
commands. After `br sync --flush-only`, you must manually
run `git add .beads/ && git commit`.

### Quick Reference

```bash
br ready              # Find available work
br show <id>          # View issue details
br update <id> --claim  # Claim work
br close <id>         # Complete work
br sync --flush-only  # Export JSONL
git add .beads/
git commit -m "sync beads"
```

### Rules

- Use `br` for ALL task tracking — do NOT use
  TodoWrite, TaskCreate, or markdown TODO lists
- Use `br remember` for persistent knowledge — do NOT
  use MEMORY.md files

<!-- END BEADS INTEGRATION -->

