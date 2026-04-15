# GPF Monorepo — Agent Guide

This file provides guidance to Claude Code when working
with code in this repository.

## Project Overview

GPF (Genotypes and Phenotypes in Families) is a system for
managing large databases of genetic variants and phenotypic
measurements from family collections (e.g., the Simons
Simplex Collection with ~2,600 autism families).

## Environment Setup

**This project requires conda/mamba.** All tools must be
installed via conda, not system pip.

```bash
mamba env create --name gpf --file ./environment.yml
mamba env update --name gpf --file ./dev-environment.yml
conda activate gpf

# Install core packages in editable mode
pip install -e gain_core
pip install -e gpf_core
pip install -e gpf_web
```

## Commands

### Testing

```bash
# Run a single test file
cd gpf_core && pytest -v tests/small/path/to/test_file.py

# Run a test module
cd gpf_core && pytest -v tests/small/module/

# Run GAIN tests in parallel
cd gain_core && pytest -v -n 10 tests/

# Run GPF tests in parallel
cd gpf_core && pytest -v -n 10 tests/

# Run GPF Web tests in parallel
cd gpf_web && pytest -v -n 5 gpf_web/
```

Test markers in `gpf_core/pytest.ini`: genotype storage
(`gs_impala`, `gs_impala2`, `gs_inmemory`, `gs_gcp`,
`gs_duckdb`, `gs_duckdb_parquet`, `gs_schema2`,
`gs_parquet` and `no_gs_*` exclusion variants) and GRR
(`grr_rw`, `grr_ro`, `grr_full`, `grr_http`, `grr_tabix`).

Test markers in `gain_core/pytest.ini`: `grr_rw`, `grr_ro`,
`grr_full`, `grr_http`, `grr_tabix`.

All tests run with `PYTHONHASHSEED=0`.

### Linting and Type Checking

```bash
# Ruff linting (fast, primary linter)
ruff check --fix .

# Type checking (slow, 2-5 minutes)
mypy gain --exclude gain_core/docs/ \
    --exclude gain_core/gain/docs/
mypy gpf --exclude gpf_core/docs/
mypy gpf_web --exclude gpf_web/docs/ \
    --exclude gpf_web/conftest.py
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
  `gain_core/tests/.test_grr/`

### Do NOT run locally

`build.sh` requires Docker and a private `build-scripts`
submodule — it's only for CI (Jenkins).

## Architecture

### Dependency Direction

Strict layering enforced by pytestarch architecture tests
(`gain_core/tests/test_architecture.py`):

```
gain_core  ←  gpf_core  ←  gpf_web
```

`gain_core` must **never** import from `gpf_core` or
`gpf_web`. `gpf_core` must **never** import from `gpf_web`.

### Package Structure

- **`gain_core/`** — GAIn (Genomic Annotation
  Infrastructure): annotation engine, genomic resources,
  effect annotation, task graph, gene scores/sets.
  Python package: `gain`.
- **`gpf_core/`** — GPF core library: genotype storage,
  studies, pedigrees, pheno, import tools, query API.
  Python package: `gpf`. Depends on `gain`.
- **`gpf_web/`** — Web application: Django REST API on
  top of GPF. Python package: `gpf_web`. Depends on
  `gpf` and `gain`.
- **`gpf_impala_storage/`**, **`gpf_impala2_storage/`**,
  **`gpf_gcp_storage/`** — optional storage backends
- **`gpf_federation/`** — federated query support
- **`rest_client/`** — REST API client library
- **`spliceai_annotator/`**,
  **`gain_vep_annotator/`**,
  **`gain_demo_annotator/`** — external annotation
  plugins (Docker-based)

### Plugin System

GPF uses Python entry points for extensibility.

**Defined in `gain_core/setup.py`:**

1. **`gain.genomic_resources.plugins`** — genomic context
   providers (DefaultRepository, CLI, CLIAnnotation)
2. **`gain.genomic_resources.implementations`** —
   position/allele/NP scores, liftover chain, genome,
   gene models, CNV collection, annotation pipeline,
   gene score, gene set collection
3. **`gain.annotation.annotators`** — all built-in
   annotator types (score, effect, gene set, liftover,
   normalize allele, CNV collection, chrom mapping,
   gene score, simple effect, debug)

**Defined in `gpf_core/setup.py`:**

4. **`gain.genomic_resources.plugins`** —
   GPFInstanceContextProvider
5. **`gain.genomic_resources.implementations`** —
   enrichment backgrounds (gene weights, Samocha)
6. **`gpf.genotype_storage.factories`** — inmemory,
   duckdb (legacy, standard, parquet, S3, S3 parquet),
   parquet
7. **`gpf.import_tools.storages`** — import storage
   backends matching each genotype storage type
   (schema2, inmemory, duckdb variants, parquet)

**Defined in `gpf_web/setup.py`:**

8. **`console_scripts`** — `wgpf` (web server launcher),
   `wdaemanage` (Django management wrapper)

### GAIN Submodules (`gain_core/gain/`)

- **`annotation/`** — annotation pipeline engine,
  annotator base classes, all built-in annotators,
  processing pipeline, annotation config parsing
- **`genomic_resources/`** — Genomic Resource Repository
  (GRR): repository hierarchy (cached, group, factory),
  resource implementations, fsspec protocol, genomic
  context system. Sub-packages:
  - `gene_models/` — gene model parsing and
    serialization
  - `genomic_position_table/` — tabular data backends
    (tabix, BigWig, VCF, in-memory)
  - `implementations/` — resource type implementations
    (scores, genome, gene models, liftover, CNV,
    annotation pipeline)
  - `statistics/` — resource statistics (min/max)
- **`effect_annotation/`** — variant effect prediction
  (effect types, effect gene/transcript annotation)
- **`task_graph/`** — DAG-based task orchestration
- **`gene_scores/`** — gene-level score resources and
  implementations
- **`gene_sets/`** — gene set collection resources and
  implementations
- **`dask/`** — dask named cluster configuration
- **`testing/`** — test fixture helpers for study import
  (acgt, alla, foobar, t4c8 datasets)
- **`utils/`** — shared utilities (fs_utils, helpers)

### GPF Core Submodules (`gpf_core/gpf/`)

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

### GPF Web Structure (`gpf_web/gpf_web/`)

The web layer is a Django project. The Django project
package is `gpf_web/gpf_web/gpf_web/` (settings, urls,
wsgi). Django apps sit at `gpf_web/gpf_web/<app_name>/`.

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

Both `gain_core` and `gpf_core` use a `tests/small/` vs
`tests/integration/` split:
- `tests/small/` — unit/fast tests (default for
  development and CI)
- `tests/integration/` — tests requiring external
  services or longer runtime

`gpf_web` unit tests live inside each Django app:
`gpf_web/gpf_web/<app>/tests/`
Integration tests are in `gpf_web/gpf_web_tests/integration/`.

Key conftest patterns:
- **`grr_scheme` parametrization** — tests tagged with
  `grr_rw`, `grr_full`, `grr_http`, `grr_tabix` markers
  are automatically parametrized across GRR protocols
  (inmemory, file, s3, http). Enable S3/HTTP with
  `--enable-s3-testing` / `--enable-http-testing`.
- **`genotype_storage_factory` parametrization** — tests
  tagged with `gs_*` markers run against the appropriate
  storage backends.
- Architecture tests in `gain_core/tests/` enforce the
  dependency direction rule via `pytestarch`.

### CLI Tools

**gain_core CLIs:**
- `grr_manage` — genomic resource repository management
- `grr_browse` — GRR browser
- `annotate_columns` / `annotate_vcf` / `annotate_doc`
  — annotation tools
- `annotate_variant_effects` /
  `annotate_variant_effects_vcf` — effect annotation

**gpf_core CLIs:**
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

**gpf_web CLIs:**
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

Settings files in `gpf_web/gpf_web/gpf_web/`:

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

