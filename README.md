# GPF: Genotypes and Phenotypes in Families

The Genotypes and Phenotypes in Families (GPF) system manages large databases
of genetic variants and phenotypic measurements from family collections.


User documentation: see the GPF documentation at
https://iossifovlab.com/gpfuserdocs/.

## Repository overview

- Core library: DAE (Data Access Environment) in `dae/`
- Web application and REST API: WDAE in `wdae/`
- Optional genotype storages: `impala_storage/`, `impala2_storage/`,
  `gcp_storage/`
- Federation and REST client: `federation/`, `rest_client/`
- Documentation sources: `docs/`

Primary stack: Python 3.12, Django 5.2, dask, pandas, pyarrow, duckdb, pysam,
pytest, mypy, ruff.

Release notes live in `docs/changes.rst`.

## Development

We recommend using a Conda/Mamba environment. All development tools
(pytest, ruff, mypy) are installed via Conda, not system pip.

### 1) Create and activate the environment

From the repository root:

```bash
mamba env create --name gpf --file ./environment.yml
mamba env update --name gpf --file ./dev-environment.yml

conda activate gpf
```

Notes:
- Prefer `environment.yml` over the legacy `requirements.txt`.
- Always activate the `gpf` environment before running tools or tests.

### 2) Install core packages in editable mode

Install GPF packages into the active `gpf` environment:

```bash
pip install -e dae
pip install -e wdae
```

Tip: after changing package code, re-run the editable installs if imports fail.

### 3) Run tests

Quick cycles (examples):

```bash
cd dae
pytest -v tests/small/test_file.py
pytest -v tests/small/module/
```

Full suites (parallel):

```bash
cd dae
conda run -n gpf pytest -v -n 10 tests/

cd ../wdae
conda run -n gpf pytest -v -n 5 wdae/
```

Test markers and configuration are defined in `dae/pytest.ini` (e.g.,
`gs_impala`, `gs_gcp`, `gs_duckdb`, `grr_rw`, `grr_ro`).

### 4) Linting and type checking

```bash
ruff check --fix .
mypy dae --exclude dae/docs/
mypy wdae --exclude wdae/docs/ --exclude wdae/conftest.py
# Optional extra checks
pylint dae/dae -f parseable --reports=no -j 4
```

### REST Client and Federation (optional)

If you want to work with `federation` and `rest_client` modules, install
additional dependencies and then the packages:

```bash
mamba env update --name gpf --file ./federation/federation-environment.yml
pip install -e rest_client
pip install -e federation
```

### Additional genotype storages (optional)

Some storages are not included in the default installation. Install their
dependencies only if you plan to use or develop them.

#### Apache Impala genotype storage

```bash
mamba env update --name gpf --file ./impala_storage/impala-environment.yml
pip install -e impala_storage
```

#### Apache Impala2 genotype storage

```bash
mamba env update --name gpf --file ./impala2_storage/impala2-environment.yml
pip install -e impala2_storage
```

#### GCP (BigQuery) genotype storage

```bash
mamba env update --name gpf --file ./gcp_storage/gcp-environment.yml
pip install -e gcp_storage
```

Authenticate for the `seqpipe-gcp-storage-testing` project before running tests:

```bash
gcloud config list project
gcloud auth application-default login
```

Run GCP storage tests (from the `gcp_storage/` directory):

```bash
pytest -v gcp_storage/tests/
```

Run integration tests against the GCP genotype storage definition:

```bash
pytest -v ../dae/tests/ --gsf gcp_storage/tests/gcp_storage.yaml
```

### Pre-commit lint check hook

A git pre-commit hook for lint checking with Ruff is included.
Install it from the repository root:

```bash
cp pre-commit .git/hooks/
```

To bypass the pre-commit hook when committing:

```bash
git commit --no-verify
```

## Common pitfalls

- Always activate the `gpf` Conda environment before running commands:
  `conda activate gpf`.
- Prefer `environment.yml` over `requirements.txt` (legacy).
- If imports fail after changes, re-run `pip install -e dae` and/or 
  `pip install -e wdae`.
- Some tests may be flaky with high parallelism; reduce `-n` or run without it.

## License

This project is licensed under the MIT License. See `LICENSE` for details.
