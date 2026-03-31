# GPF: Genotypes and Phenotypes in Families

The Genotypes and Phenotypes in Families (GPF) system manages large databases of genetic variants and phenotypic measurements from family collections. This is a Python-based monorepo with multiple sub-packages and specialized genotype storage backends.

## Project Architecture

- **`dae/`**: Core library (Data Access Environment). Handles data access, variant processing, and core logic.
- **`wdae/`**: Web application and REST API (Django-based). Provides the user interface and public API.
- **Genotype Storages**: Specialized backends for genomic data:
  - `impala_storage/`, `impala2_storage/`: Apache Impala backends.
  - `gcp_storage/`: Google Cloud Platform (BigQuery) backend.
  - `impala2_storage/`: DuckDB based storage.
- **`federation/` & `rest_client/`**: Tools for federating multiple GPF instances and interacting with them via REST.
- **Annotators**: Specialized modules for genomic annotation:
  - `external_demo_annotator/`, `external_vep_annotator/`, `spliceai_annotator/`.

## Technology Stack

- **Language**: Python 3.12
- **Web Framework**: Django 5.2, Django REST Framework
- **Data Processing**: Dask, Pandas, Pyarrow, DuckDB, Polars
- **Genomic Tools**: Pysam, BCFtools, Samtools
- **Testing**: Pytest
- **Linting & Typing**: Ruff, Mypy, Pylint
- **Environment Management**: Conda/Mamba

## Development Workflow

### Environment Setup

We strictly use Conda/Mamba for environment management.

```bash
# Create and update the environment
mamba env create --name gpf --file environment.yml
mamba env update --name gpf --file dev-environment.yml

# Activate the environment
conda activate gpf

# Install core packages in editable mode
pip install -e dae
pip install -e wdae
```

### Building and Running

The project uses `build.sh` for automated build and diagnostic cycles, which often involve Docker for isolated testing environments.

- **Full Build**: `./build.sh`
- **Cleanup**: `./build_cleanup.sh`

### Testing

Tests are managed by `pytest`. Use markers to skip or include specific storage tests.

- **DAE tests**: `pytest dae/tests/` (often run with `-n` for parallelism)
- **WDAE tests**: `pytest wdae/wdae/`
- **Storage-specific tests**: See `README.md` for specific `environment.yml` and `pip install` commands for optional storages.

### Linting and Type Checking

Strict linting and typing are enforced.

- **Ruff**: `ruff check .` (config in `ruff.toml`, line-length 80)
- **Mypy**: `mypy dae` and `mypy wdae` (config in `mypy.ini`)
- **Pylint**: `pylint dae/dae` (config in `pylintrc`)

## Development Conventions

- **Code Style**: Adhere to PEP8 via Ruff. Inline, docstring, and multiline quotes should be double (`"`).
- **Type Hints**: Mandatory for `dae/` and `wdae/`. Use `mypy` to validate.
- **Imports**: Sorted via Ruff's `I` (isort) rule.
- **Tests**: Every new feature or bug fix must include tests. Use `pytest` and follow existing patterns in `dae/tests/` or `wdae/wdae/tests/`.
- **Git Hook**: A pre-commit hook is provided in `pre-commit`. Install it with `cp pre-commit .git/hooks/`.

## Key Files

- `environment.yml`: Primary Conda dependencies.
- `dev-environment.yml`: Development-specific dependencies (linting, testing).
- `ruff.toml`: Ruff linting configuration.
- `mypy.ini`: Mypy static analysis configuration.
- `build.sh`: Main build and CI orchestration script.
- `Dockerfile.seqpipe`: Base Dockerfile for GPF environments.
