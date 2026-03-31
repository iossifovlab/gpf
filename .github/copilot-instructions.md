# GPF: Genotypes and Phenotypes in Families - Copilot Instructions

## Repository Overview

**GPF** is a system for managing large databases of genetic variants and
phenotypic measurements from family collections (e.g., the Simons Simplex
Collection with ~2,600 autism families).

- Primary language: Python 3.12
- Framework: Django 5.2 (web), pytest for testing

## Project Structure

### Core Packages

- **gain/** — Genomic Annotation Infrastructure (Python package: `gain`)
  - `gain/gain/` — annotation pipeline engine, genomic resource repository
    (GRR), effect annotation, task graph, gene scores/sets
  - Foundation layer; no dependency on `gpf` or `wdae`

- **gpf/** — GPF core library (Python package: `gpf`, setup name: `gpf_dae`)
  - `gpf/gpf/` — genotype storage, variants, studies, pedigrees, pheno,
    enrichment tool, import tools, query API
  - Depends on `gain` for annotation and genomic resources

- **wdae/** — Web Django Application (Python package: `wdae`)
  - `wdae/wdae/` — Django REST API (28+ apps: `datasets_api`,
    `genotype_browser`, `users_api`, `gene_profiles_api`, etc.)
  - Depends on both `gain` and `gpf`

**Dependency order:** `gain` → `gpf` → `wdae`

### Optional Storage Backends

- **impala_storage/**, **impala2_storage/** — Apache Impala backends
- **gcp_storage/** — Google Cloud Platform/BigQuery backend

### Other Modules

- **federation/**, **rest_client/** — federated query support and REST client
- **external_demo_annotator/**, **external_vep_annotator/**,
  **spliceai_annotator/** — external annotation plugins

## Environment Setup

**CRITICAL:** This project requires conda/mamba. All development tools
(pytest, ruff, mypy) are installed via conda, NOT system pip.

```bash
mamba env create --name gpf --file ./environment.yml
mamba env update --name gpf --file ./dev-environment.yml
conda activate gpf

pip install -e gain
pip install -e gpf
pip install -e wdae
```

### Optional Storage Modules

```bash
# Impala storage
mamba env update --name gpf --file ./impala_storage/impala-environment.yml
pip install -e impala_storage

# Impala2 storage
mamba env update --name gpf --file ./impala2_storage/impala2-environment.yml
pip install -e impala2_storage

# GCP storage
mamba env update --name gpf --file ./gcp_storage/gcp-environment.yml
pip install -e gcp_storage
gcloud auth application-default login  # Required for GCP tests
```

### Optional Federation Module

```bash
mamba env update --name gpf --file ./federation/federation-environment.yml
pip install -e rest_client
pip install -e federation
```

## Build, Test, and Lint

### Running Tests

```bash
# Single test file
cd gpf && pytest -v tests/small/path/to/test_file.py

# Single test module
cd gpf && pytest -v tests/small/module/

# GAIN tests (parallel)
cd gain && pytest -v -n 10 tests/

# GPF core tests (parallel, ~10-15 min)
cd gpf && pytest -v -n 10 tests/

# WDAE tests (parallel, ~5-10 min)
cd wdae && pytest -v -n 5 wdae/

# Skip storage-specific tests locally
pytest -m "not gs_impala and not gs_gcp"
```

**Test markers** (in `gpf/pytest.ini` and `gain/pytest.ini`):
- Storage: `gs_impala`, `gs_impala2`, `gs_inmemory`, `gs_gcp`, `gs_duckdb`,
  `gs_duckdb_parquet`, `gs_schema2`, `gs_parquet` (and `no_gs_*` negations)
- GRR protocols: `grr_rw`, `grr_ro`, `grr_full`, `grr_http`, `grr_tabix`
- Tests run with `PYTHONHASHSEED=0` for deterministic behavior
- Both `gpf/pytest.ini` and `gain/pytest.ini` set `addopts = -p no:django`

### Linting

```bash
# Ruff (primary linter) — auto-fix
ruff check --fix .

# Full ruff check excluding generated/legacy paths
ruff check --exclude impala_storage --exclude impala2_storage \
  --exclude typings --exclude migrations --exclude docs \
  --exclude versioneer.py --exclude _version.py --exclude "*.ipynb" .

# Type checking (2-5 minutes each)
mypy gain --exclude gain/docs/
mypy gpf --exclude gpf/docs/
mypy wdae --exclude wdae/docs/ --exclude wdae/conftest.py

# Pylint (secondary, legacy)
pylint gpf/gpf -f parseable --reports=no -j 4
```

Config: `ruff.toml` (line-length: 80, target: py310), `mypy.ini` (strict,
Django plugin), `pylintrc`.

### Pre-commit Hook

```bash
cp pre-commit .git/hooks/
# To bypass: git commit --no-verify
```

## Architecture

### Plugin System

GPF uses Python entry points for extensibility. **All entry point group names
use the `dae.*` prefix** for backward compatibility, even in `gain`.

| Group | Defined in | Purpose |
|---|---|---|
| `dae.genomic_resources.plugins` | gain, gpf | GRR context providers |
| `dae.genomic_resources.implementations` | gain, gpf | Resource type handlers (scores, genome, gene models, etc.) |
| `dae.annotation.annotators` | gain | Annotator factories (score, effect, gene set, liftover, etc.) |
| `dae.genotype_storage.factories` | gpf | Storage backends (duckdb, parquet, inmemory, etc.) |
| `dae.import_tools.storages` | gpf | Import storage backends |

Plugins are lazily loaded at runtime via `importlib.metadata.entry_points()`.
To add a new storage backend, register a factory in the
`dae.genotype_storage.factories` entry point group.

### Genotype Storage Factory Pattern

`gpf/gpf/genotype_storage/` uses a registry loaded from entry points:

```python
# All storage backends registered as entry points:
# [dae.genotype_storage.factories]
# duckdb = gpf.duckdb_storage.duckdb_genotype_storage:duckdb_storage_factory

class GenotypeStorage(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def get_storage_types(cls) -> set[str]: ...
```

Built-in storage types: `inmemory`, `duckdb`, `duckdb_parquet`,
`duckdb_s3`, `duckdb_s3_parquet`, `parquet`, `duckdb_legacy`.

### WDAE API Pattern

All variant query endpoints extend `QueryBaseView`:

```python
class QueryBaseView(views.APIView):
    authentication_classes = (GPFOAuth2Authentication,)
    # Uses query/response transformers for normalization
    # Uses IsDatasetAllowed for per-dataset permission checks
    # Large result sets use StreamingHttpResponse
```

`WGPFInstance` is the web-layer wrapper around the core `GPFInstance`.
Django settings files in `wdae/wdae/wdae/`: `settings.py`,
`test_settings.py`, `default_settings.py`, `gunicorn_settings.py`,
`mypy_settings.py`.

### Data Flow

```
REST Request → WDAE Django App
                → QueryTransformer (request normalization)
                → GPFInstance / study (gpf core)
                    → Genotype Storage (DuckDB / Parquet / Impala)
                    → Annotation Engine (gain)
                    → Genomic Resource Repository (gain)
                → ResponseTransformer (result formatting)
              → StreamingHttpResponse
```

## Key Conventions

- **Type hints:** Mandatory for `gain/`, `gpf/`, and `wdae/`. Mypy strict mode enforced.
- **Imports:** Sorted via Ruff's `I` rule.
- **Quotes:** Use double quotes (`"`) for strings, docstrings, and multiline strings.
- **Line length:** 80 characters (configured in `ruff.toml`).
- **Version management:** Uses versioneer for git-based versioning.
  Auto-generated files (`*/_version.py`) — do not edit.
- **Migrations:** `*/migrations/*.py` are excluded from linting.
- **Build artifacts:** Ignore `build/`, `dist/`, `*.egg-info/`, `__pycache__/`.

## Common Pitfalls

1. **Conda environment MUST be activated** before any command. Tools are not
   on the system PATH.

2. **`requirements.txt` is legacy** (Python 3.11). Use `environment.yml`
   (Python 3.12) for development.

3. **After code changes**, re-install the affected package:
   ```bash
   pip install -e gain   # if you changed gain/
   pip install -e gpf    # if you changed gpf/
   pip install -e wdae   # if you changed wdae/
   ```

4. **Parallel test flakiness:** Reduce `-n 10` to `-n 5` or drop `-n` for
   debugging.

5. **GCP tests** require `gcloud auth application-default login`.

6. **Impala tests** require a running Impala instance; skip locally with
   `-m "not gs_impala"`.

7. **DO NOT run `build.sh` locally** — it requires Docker and a private
   `build-scripts` submodule (CI/Jenkins only).

## CI/CD

Jenkins pipeline (`Jenkinsfile`) via `build.sh`:
- Uses Docker images based on `condaforge/mambaforge`
- Spins up localstack (S3) and Apache (HTTP) containers for integration tests
- Runs ruff, pylint, mypy diagnostics in parallel
- Runs gain, gpf, wdae, and annotator tests in parallel (`-n 10`/`-n 5`)
- Env vars: `GRR_DEFINITION_FILE`, `HTTP_HOST`, `LOCALSTACK_HOST`
- Coverage combined from `gain/.coverage`, `gpf/.coverage`, `wdae/.coverage`
