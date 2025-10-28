# GPF: Genotypes and Phenotypes in Families - Copilot Instructions

## Repository Overview

**GPF** is a system for managing large databases of genetic variants and phenotypic measurements from family collections. The main application manages data from the Simons Simplex Collection (~2,600 families with autism diagnoses).

**Key Stats:**
- ~1,000+ Python files across core packages
- Primary language: Python 3.12
- Framework: Django 5.2 (web), pytest for testing
- Size: ~50MB codebase (dae: 14MB, wdae: 3.1MB, impala_storage: 29MB)

## Project Structure

### Core Modules

- **dae/** - Data Access Environment (DAE), core library for genetic data analysis
  - `dae/dae/` - Main source (35+ subpackages: genomic_resources, genotype_storage, variants, pedigrees, etc.)
  - `dae/tests/` - 442+ test files organized in `small/` and `integration/` subdirectories
  - Key areas: annotation, genomic_resources, genotype_storage, import_tools, parquet_storage

- **wdae/** - Web Django Application Environment
  - `wdae/wdae/` - Django REST API (28+ apps: datasets_api, genotype_browser, users_api, etc.)
  - `wdae/wdae_tests/` - 88+ integration test files
  - Main Django app with REST endpoints for variant browsing and analysis

### Storage Implementations (Optional)

- **impala_storage/** - Apache Impala genotype storage (29MB, largest module)
- **impala2_storage/** - Apache Impala2 genotype storage
- **gcp_storage/** - Google Cloud Platform/BigQuery storage
- **federation/** - Federated query support
- **rest_client/** - REST API client library

### Other Modules

- **external_demo_annotator/** - Demo external annotation plugin
- **external_vep_annotator/** - VEP annotation plugin
- **spliceai_annotator/** - SpliceAI annotation plugin

## Environment Setup

**CRITICAL:** This project requires conda/mamba. All development tools (pytest, ruff, mypy) are installed via conda, NOT system pip.

### Initial Setup (Required)

```bash
# Create conda environment with dependencies
mamba env create --name gpf --file ./environment.yml
mamba env update --name gpf --file ./dev-environment.yml

# Activate environment (REQUIRED for all commands)
conda activate gpf

# Install core packages in development mode
for d in dae wdae; do (cd $d; pip install -e .); done
```

### Optional Storage Modules

Only install if working with specific storage backends:

```bash
# For Impala storage
mamba env update --name gpf --file ./impala_storage/impala-environment.yml
pip install -e impala_storage

# For Impala2 storage
mamba env update --name gpf --file ./impala2_storage/impala2-environment.yml
pip install -e impala2_storage

# For GCP storage
mamba env update --name gpf --file ./gcp_storage/gcp-environment.yml
pip install -e gcp_storage
gcloud auth application-default login  # Required for GCP tests

# For Federation and REST client
mamba env update --name gpf --file ./federation/federation-environment.yml
pip install -e rest_client
pip install -e federation
```

## Build, Test, and Lint

### Running Tests

**IMPORTANT:** Tests use pytest with parallel execution. The conda environment MUST be activated.

```bash
# Core dae tests (takes ~10-15 minutes with parallel execution)
cd dae
conda run -n gpf pytest -v -n 10 tests/

# Web application (wdae) tests (takes ~5-10 minutes)
cd wdae
conda run -n gpf pytest -v -n 5 wdae/

# GCP storage tests (requires authentication)
cd gcp_storage
conda run -n gpf pytest -v gcp_storage/tests/
conda run -n gpf pytest -v ../dae/tests/ --gsf gcp_storage/tests/gcp_storage.yaml
```

**Test Configuration:**
- `dae/pytest.ini` - Main pytest configuration with genotype storage markers
- Markers: `gs_impala`, `gs_gcp`, `gs_duckdb`, `grr_rw`, `grr_ro`, etc.
- Tests run with `PYTHONHASHSEED=0` for deterministic behavior

### Linting

**CRITICAL:** Always run linting before committing. Use ruff (primary) and the pre-commit hook.

```bash
# Run ruff (primary linter) - FAST
conda run -n gpf ruff check --exclude impala_storage --exclude impala2_storage \
  --exclude typings --exclude migrations --exclude docs --exclude wdae_tests \
  --exclude versioneer.py --exclude _version.py --exclude "*.ipynb" .

# Auto-fix ruff issues
conda run -n gpf ruff check --fix .

# Run mypy (type checking) - takes 2-5 minutes
conda run -n gpf mypy dae --exclude dae/docs/
conda run -n gpf mypy wdae --exclude wdae/docs/ --exclude wdae/conftest.py

# Run pylint (additional checks)
conda run -n gpf pylint dae/dae -f parseable --reports=no -j 4
```

**Lint Configuration:**
- `ruff.toml` - Primary linting rules (line-length: 80, target: py310)
- `mypy.ini` - Type checking with strict settings, uses Django plugin
- `pylintrc` - Legacy linting configuration
- `pre-commit` - Git hook script for ruff validation

### Pre-commit Hook

Install the pre-commit hook to catch linting issues early:

```bash
cp pre-commit .git/hooks/
# To bypass: git commit --no-verify
```

## CI/CD Pipeline

### Jenkins Build (Jenkinsfile)

The project uses a complex Jenkins pipeline with Docker containers. DO NOT attempt to replicate locally.

**Build Script:** `build.sh` orchestrates the full build:
1. Cleanup stage
2. Get GPF version
3. Create gpf-dev Docker image
4. Run localstack (for S3 testing)
5. Run Apache (for HTTP testing)
6. Diagnostics (ruff, pylint, mypy in parallel)
7. Tests (dae, wdae, demo_annotator, vep_annotator in parallel with pytest -n 10/5)
8. Package stage

**Key Build Details:**
- Uses custom Docker images based on `condaforge/mambaforge`
- Network setup with localstack and Apache containers
- Environment variables: `GRR_DEFINITION_FILE`, `HTTP_HOST`, `LOCALSTACK_HOST`
- Tests run in parallel Docker containers with shared network
- Coverage reports combined from dae/.coverage and wdae/.coverage
- Results in `test-results/`: junit XML, coverage XML, HTML reports

**DO NOT RUN `build.sh` locally** - it requires build-scripts submodule and Docker infrastructure.

## Configuration Files

### Root Level
- `environment.yml` - Conda production dependencies (Python 3.12, Django 5.2, pysam, dask, etc.)
- `dev-environment.yml` - Development tools (pytest, ruff 0.14.0, mypy 1.18, pylint, sphinx)
- `requirements.txt` - Legacy conda requirements (Python 3.11, older versions)
- `ruff.toml` - Linting configuration
- `mypy.ini` - Type checking configuration
- `pylintrc` - Pylint configuration
- `coveragerc` - Coverage configuration (omits tests, _version.py, docs)
- `.gitmodules` - build-scripts submodule (private repo, not needed for development)

### Package Level
- `dae/setup.py`, `wdae/setup.py` - Package definitions using versioneer
- `dae/pytest.ini` - Test markers and configuration
- Each storage module has its own `setup.py` and environment YAML

## Common Pitfalls and Workarounds

### Critical Issues

1. **Conda environment MUST be activated** - All tools only work within conda environment:
   ```bash
   conda activate gpf  # Before ANY command
   ```

2. **Python version mismatch** - environment.yml uses Python 3.12, requirements.txt uses 3.11:
   - Use `environment.yml` (newer) for development
   - Ignore `requirements.txt` (legacy)

3. **Import errors after code changes**:
   - Re-run: `pip install -e dae` and/or `pip install -e wdae`
   - Check you're in the correct conda environment

4. **Test failures with parallel execution**:
   - Some tests may be flaky with `-n 10`, reduce to `-n 5` or remove `-n` flag
   - Set `PYTHONHASHSEED=0` for deterministic behavior

5. **Ruff vs Pylint conflicts**:
   - Ruff is primary (faster, modern)
   - Pylint is secondary (legacy)
   - Follow ruff recommendations first

### Build Script Warnings

- DO NOT run `build.sh` without Docker and build-scripts submodule
- The build-scripts submodule is from a private repo (ssh://git@github.com/seqpipe/build-scripts.git)
- Use manual conda commands for local development instead

### Storage Module Testing

- GCP tests require `gcloud auth application-default login`
- Impala tests may require actual Impala instance (often skipped in local dev)
- Use markers to skip: `pytest -m "not gs_impala and not gs_gcp"`

## Making Changes

### Typical Workflow

1. **Activate environment:**
   ```bash
   conda activate gpf
   ```

2. **Make code changes** in `dae/dae/` or `wdae/wdae/`

3. **Run relevant tests immediately:**
   ```bash
   cd dae
   pytest -v tests/small/test_file.py  # Single file
   pytest -v tests/small/module/  # Module
   ```

4. **Lint your changes:**
   ```bash
   ruff check --fix path/to/changed/file.py
   ```

5. **Type check if modifying type annotations:**
   ```bash
   mypy dae/dae/module/
   ```

6. **Run full test suite before PR:**
   ```bash
   pytest -v -n 10 dae/tests/
   pytest -v -n 5 wdae/wdae/
   ```

### File Patterns to Ignore

- `dae/dae/_version.py`, `wdae/wdae/_version.py` - Auto-generated by versioneer
- `dae/dae/__build__.py`, `wdae/wdae/__build__.py` - Build-time generated
- `*/migrations/*.py` - Django migrations (excluded from linting)
- `docs/` - Documentation (separate build process)
- `build/`, `dist/`, `*.egg-info/` - Build artifacts

## Key Dependencies

**Production:**
- pysam 0.23.3 (SAM/BAM file handling)
- Django 5.2.5 (web framework)
- dask 2025.4.1 (parallel computing)
- pandas 2.2.3, numpy 2.2.6 (data analysis)
- duckdb 1.4.1 (embedded database)
- pyarrow >=18 (columnar data)

**Development:**
- pytest 8.3 (testing)
- pytest-xdist 3.6 (parallel testing)
- ruff 0.14.0 (linting)
- mypy 1.18 (type checking)
- coverage 7.6 (test coverage)

## Additional Notes

- **Documentation:** Built with Sphinx, see `docs/` and `build_docs.sh`
- **Version management:** Uses versioneer for git-based versioning
- **Django settings:** wdae uses custom mypy_settings for django-stubs
- **Logging:** Check for sentry-sdk integration in production code
- **Security:** OAuth2 toolkit used for authentication
- **Performance:** Parallel processing via dask, parquet for storage

---

**When in doubt:** Check `README.md` first, then this file, then ask for clarification. Trust these instructions and minimize exploration when the information is already documented here.
