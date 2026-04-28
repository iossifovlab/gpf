# GPF: Genotypes and Phenotypes in Families

The Genotypes and Phenotypes in Families (GPF) system
manages large databases of genetic variants and phenotypic
measurements from family collections.

User documentation: see the GPF documentation at
https://iossifovlab.com/gpfuserdocs/.

## Repository overview

- **`core/`** — GPF core library: genotype storage,
  studies, pedigrees, pheno, import tools, query API.
  Python package: `gpf`. Depends on `gain`.
- **`web/`** — Web application and REST API
  (Django 5.2). Python package: `gpf_web`. Depends on
  `gpf` and `gain`.
- **`impala_storage/`**, **`impala2_storage/`**,
  **`gcp_storage/`** — optional genotype storages
- **`federation/`**, **`rest_client/`** — federation and
  REST client
- **`docs/`** — documentation sources

The `gain` package (annotation engine, genomic resources,
effect annotation, task graph, gene scores/sets) lives in
its own repository at
<https://github.com/iossifovlab/gain>.

Primary stack: Python 3.12, Django 5.2, dask, pandas,
pyarrow, duckdb, pysam, pytest, mypy, ruff.

Release notes live in `docs/changes.rst`.

## Development

Two supported workflows: Conda/Mamba (long-standing) and
uv (pyproject-driven). Pick one.

The `gain` package lives in a separate repository
(<https://github.com/iossifovlab/gain>) and must be
checked out and installed alongside this one before the
GPF packages will import:

```bash
git clone https://github.com/iossifovlab/gain.git ../gain
```

### Option A: Conda/Mamba

```bash
mamba env create --name gpf --file ./environment.yml
mamba env update --name gpf --file ./dev-environment.yml
conda activate gpf

pip install -e ../gain/core
pip install -e core
pip install -e web

# Optional storages and extensions:
pip install -e federation
pip install -e rest_client
pip install -e gcp_storage
pip install -e impala_storage
pip install -e impala2_storage
```

Notes:
- Always activate the `gpf` environment before running
  tools or tests.
- After changing package code, re-run the editable
  installs if imports fail.

### Option B: uv workspace

This repo is a uv workspace (see root `pyproject.toml`).
Runtime dependencies are declared per sub-project; dev
tools live in each sub-project's own `dev` dependency
group. The root `pyproject.toml` is a virtual coordinator
(`[tool.uv] package = false`) that defaults to installing
just `gpf-core` + `gpf-web` — the storage backends and
the federation/rest_client extensions are workspace
members but optional.

```bash
# Default: install gpf-core + gpf-web
uv sync

# Everything: all workspace members + every dev group
uv sync --all-packages --all-groups

# A single sub-project
uv sync --package gpf-impala-storage --group dev

# Activate the venv (optional; `uv run` works without it)
source .venv/bin/activate
```

The lockfile (`uv.lock`) is committed. Use `uv lock
--upgrade` to refresh.

### Run tests

Quick cycles (examples):

```bash
cd core
pytest -v tests/small/test_file.py
pytest -v tests/small/module/
```

Full suites (parallel):

```bash
cd core
conda run -n gpf pytest -v -n 10 tests/

cd ../web
conda run -n gpf pytest -v -n 5 gpf_web/
```

Test markers and configuration are defined in
`core/pytest.ini` (e.g., `gs_inmemory`, `gs_duckdb`,
`gs_duckdb_parquet`, `grr_rw`, `grr_ro`, `grr_http`).

### Linting and type checking

```bash
ruff check --fix .
mypy gpf --exclude core/docs/
mypy gpf_web --exclude web/docs/ \
    --exclude web/conftest.py
```

### Optional genotype storages

Install storage backends with extra conda dependencies if
you plan to use or develop them.

#### Apache Impala genotype storage

```bash
mamba env update --name gpf \
    --file ./impala_storage/impala-environment.yml
pip install -e impala_storage
```

#### Apache Impala2 genotype storage

```bash
mamba env update --name gpf \
    --file ./impala2_storage/impala2-environment.yml
pip install -e impala2_storage
```

#### GCP (BigQuery) genotype storage

```bash
mamba env update --name gpf \
    --file ./gcp_storage/gcp-environment.yml
pip install -e gcp_storage
```

Authenticate for the `seqpipe-gcp-storage-testing` project
before running tests:

```bash
gcloud config list project
gcloud auth application-default login
```

Run GCP storage tests (from the `gcp_storage/` directory):

```bash
pytest -v gcp_storage/tests/
```

Run integration tests against the GCP genotype storage
definition:

```bash
pytest -v ../core/tests/ \
    --gsf gcp_storage/tests/gcp_storage.yaml
```

### Pre-commit lint check hook

A git pre-commit hook for lint checking with Ruff is
included. Install it from the repository root:

```bash
cp pre-commit .git/hooks/
```

To bypass the pre-commit hook when committing:

```bash
git commit --no-verify
```

## Common pitfalls

- Conda users: always activate the `gpf` environment
  before running commands (`conda activate gpf`), and
  re-run `pip install -e core` if imports fail.
- uv users: prefer `uv run <cmd>` over activating the
  venv, and re-run `uv sync` (or `uv sync --all-packages
  --all-groups` if you've installed the optional
  workspace members) after pulling changes to pick up
  lockfile updates.
- If `gain` imports fail, re-install gain from its
  sibling checkout (`pip install -e ../gain/core`).
- Some tests may be flaky with high parallelism; reduce
  `-n` or run without it.

## License

This project is licensed under the MIT License. See
`LICENSE` for details.
