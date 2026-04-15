# GPF: Genotypes and Phenotypes in Families

The Genotypes and Phenotypes in Families (GPF) system
manages large databases of genetic variants and phenotypic
measurements from family collections.

User documentation: see the GPF documentation at
https://iossifovlab.com/gpfuserdocs/.

## Repository overview

- **`gain_core/`** — GAIn (Genomic Annotation
  Infrastructure): annotation engine, genomic resources,
  effect annotation, task graph, gene scores/sets.
  Python package: `gain`.
- **`gpf_core/`** — GPF core library: genotype storage,
  studies, pedigrees, pheno, import tools, query API.
  Python package: `gpf`. Depends on `gain`.
- **`gpf_web/`** — Web application and REST API
  (Django 5.2). Python package: `gpf_web`. Depends on
  `gpf` and `gain`.
- **`impala_storage/`**, **`impala2_storage/`**,
  **`gpf_gcp_storage/`** — optional genotype storages
- **`gpf_federation/`**, **`rest_client/`** — federation and
  REST client
- **`spliceai_annotator/`**,
  **`gain_vep_annotator/`**,
  **`gain_demo_annotator/`** — external annotation
  plugins
- **`docs/`** — documentation sources

Primary stack: Python 3.12, Django 5.2, dask, pandas,
pyarrow, duckdb, pysam, pytest, mypy, ruff.

Release notes live in `docs/changes.rst`.

## Development

We recommend using a Conda/Mamba environment. All
development tools (pytest, ruff, mypy) are installed via
Conda, not system pip.

### 1) Create and activate the environment

From the repository root:

```bash
mamba env create --name gpf --file ./environment.yml
mamba env update --name gpf --file ./dev-environment.yml

conda activate gpf
```

Notes:
- Prefer `environment.yml` over the legacy
  `requirements.txt`.
- Always activate the `gpf` environment before running
  tools or tests.

### 2) Install core packages in editable mode

Install GPF packages into the active `gpf` environment:

```bash
pip install -e gain_core
pip install -e gpf_core
pip install -e gpf_web
```

Tip: after changing package code, re-run the editable
installs if imports fail.

### 3) Run tests

Quick cycles (examples):

```bash
cd gpf_core
pytest -v tests/small/test_file.py
pytest -v tests/small/module/
```

Full suites (parallel):

```bash
cd gain_core
conda run -n gpf pytest -v -n 10 tests/

cd ../gpf_core
conda run -n gpf pytest -v -n 10 tests/

cd ../gpf_web
conda run -n gpf pytest -v -n 5 gpf_web/
```

Test markers and configuration are defined in
`gain_core/pytest.ini` and `gpf_core/pytest.ini` (e.g.,
`gs_inmemory`, `gs_duckdb`, `gs_duckdb_parquet`,
`grr_rw`, `grr_ro`, `grr_http`).

### 4) Linting and type checking

```bash
ruff check --fix .
mypy gain --exclude gain_core/docs/ \
    --exclude gain_core/gain/docs/
mypy gpf --exclude gpf_core/docs/
mypy gpf_web --exclude gpf_web/docs/ \
    --exclude gpf_web/conftest.py
```

### REST Client and Federation (optional)

If you want to work with `gpf_federation` and `rest_client`
modules, install additional dependencies and then the
packages:

```bash
mamba env update --name gpf \
    --file ./gpf_federation/federation-environment.yml
pip install -e rest_client
pip install -e gpf_federation
```

### Additional genotype storages (optional)

Some storages are not included in the default installation.
Install their dependencies only if you plan to use or
develop them.

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

Run GCP storage tests (from the `gpf_gcp_storage/` directory):

```bash
pytest -v gcp_storage/tests/
```

Run integration tests against the GCP genotype storage
definition:

```bash
pytest -v ../gpf_core/tests/ \
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

- Always activate the `gpf` Conda environment before
  running commands: `conda activate gpf`.
- Prefer `environment.yml` over `requirements.txt`
  (legacy).
- If imports fail after changes, re-run
  `pip install -e gain_core`, `pip install -e gpf_core`,
  and/or `pip install -e gpf_web`.
- Some tests may be flaky with high parallelism; reduce
  `-n` or run without it.

## License

This project is licensed under the MIT License. See
`LICENSE` for details.
