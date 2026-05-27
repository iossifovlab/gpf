# GPF: Genotypes and Phenotypes in Families

The Genotypes and Phenotypes in Families (GPF) system
manages large databases of genetic variants and phenotypic
measurements from family collections.

User documentation: see the GPF documentation at
https://iossifovlab.com/gpfdocs/.

## Repository overview

- **`core/`** — GPF core library: genotype storage,
  studies, pedigrees, pheno, import tools, query API.
  Python package: `gpf`. Depends on `gain`.
- **`web_api/`** — Web application and REST API
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

`uv` is the primary supported workflow — it is what CI
and the production image build use (the four CI test
images and `web_api/Dockerfile.production`). The same path
works for local development. `Conda/Mamba` is supported
as an alternative for local development only; CI does
not consume conda.

The `gain` package lives in a separate repository
(<https://github.com/iossifovlab/gain>) and must be
checked out as a sibling before either workflow will
import it:

```bash
git clone https://github.com/iossifovlab/gain.git ../gain
```

### Option A: uv (recommended)

This repo is a uv workspace (see root `pyproject.toml`).
Runtime dependencies are declared per sub-project; dev
tools live in each sub-project's own `dev` dependency
group. The root `pyproject.toml` is a virtual coordinator
(`[tool.uv] package = false`) that defaults to installing
just `gpf-core` + `gpf-web`. The `federation/` and
`rest_client/` extensions are workspace members but
optional; the heavy storage backends (`impala_storage/`,
`impala2_storage/`, `gcp_storage/`) are deliberately not
workspace members and install standalone (see "Optional
genotype storages" below).

`gain-core` is consumed as a wheel produced by gain's CI
rather than as a sibling-repo path source. Build a fresh
wheel before the first sync (and again whenever you pull
new gain master, unless you opt into editable gain — see
"gain-core: wheel install vs editable" below):

```bash
cd ../gain
uv build --package gain-core --out-dir ../gpf/dist/gain
cd ../gpf
```

Common sync invocations (all require `--find-links
./dist/gain` so uv can resolve gain-core):

```bash
# Default: install gpf-core + gpf-web
uv sync --find-links ./dist/gain

# Everything: all workspace members + every dev group
uv sync --find-links ./dist/gain --all-packages --all-groups

# A single workspace member
uv sync --find-links ./dist/gain --package gpf-federation --group dev

# Activate the venv (optional; `uv run` works without it)
source .venv/bin/activate
```

Run any command in the project's environment without
activation via `uv run`:

```bash
uv run pytest -v tests/small/
uv run ruff check --fix .
uv run mypy gpf --exclude core/docs/
```

Manage dependencies via uv (don't edit `pyproject.toml`
deps directly — uv updates the lockfile in step):

```bash
# Add a runtime dep to a workspace member
cd core && uv add <dep>

# Add a dev dep
cd core && uv add --group dev <dep>

# Remove a dep
cd core && uv remove <dep>

# Refresh the entire lockfile
uv lock --upgrade

# Refresh just one dep
uv lock --upgrade-package <dep>
```

The lockfile (`uv.lock`) is committed and managed by uv.
After `git pull`, re-run `uv sync --find-links ./dist/gain`
(plus `--all-packages --all-groups` if you've installed
the optional extensions) to pick up lockfile updates.

### gain-core: wheel install vs editable

`gain-core` is **not** on PyPI and **no longer pinned to
a sibling-repo path source** in `pyproject.toml` (it used
to be — that pattern caused tb-eqh, where docker layer
caching of `RUN git clone gain ... checkout master`
served stale gain code across CI builds).

The committed model: `gain-core` is consumed as a wheel
that gets dropped into `dist/gain/` and resolved via
`uv sync --find-links ./dist/gain`. CI provides the
wheel automatically; local devs have two choices.

#### CI

The gpf Jenkinsfile's `Fetch gain wheel` stage uses
`copyArtifacts` to pull `gain-core-*.whl` from
`iossifovlab/gain/master`'s last successful build into
`dist/gain/` before any docker build runs. Each CI
Dockerfile then `COPY`s that wheel into the image and
syncs against it. Wheel filenames encode the gain SHA
(via `hatch-vcs`), so a moving gain master invalidates
the docker layer cache by content — no more stale-clone
class of bugs.

#### Local dev — wheel from sibling clone (matches CI)

If you don't need editable gain (e.g. you're working on
gpf only, gain is read-only):

```bash
# Build a fresh gain wheel into gpf/dist/gain/
cd ../gain
uv build --package gain-core --out-dir ../gpf/dist/gain
cd ../gpf
uv sync --find-links ./dist/gain
```

Re-run the `uv build` step whenever you pull new gain
master to refresh the wheel.

#### Editable gain for local development

If you're working across both repos and want gain edits
to take effect without rebuilding a wheel, opt into the
editable path source via the local override file:

```bash
# 1. Copy the template (once per checkout):
cp pyproject.local.toml.template pyproject.local.toml
# pyproject.local.toml is gitignored.

# 2. Tell git to ignore future local edits to pyproject.toml,
#    then merge in the override block from your local file:
git update-index --skip-worktree pyproject.toml
python -c "
import pathlib, tomllib, tomlkit
base = tomlkit.parse(pathlib.Path('pyproject.toml').read_text())
local = tomllib.loads(pathlib.Path('pyproject.local.toml').read_text())
for pkg, src in local.get('tool', {}).get('uv', {}).get('sources', {}).items():
    base['tool']['uv']['sources'][pkg] = src
pathlib.Path('pyproject.toml').write_text(tomlkit.dumps(base))
"

# 3. Sync — uv will now use the editable path source for gain-core.
uv sync
```

To revert to the canonical (CI-shaped) state — e.g.
before opening a PR:

```bash
git update-index --no-skip-worktree pyproject.toml
git checkout -- pyproject.toml uv.lock
```

The `skip-worktree` bit prevents `git status`/`git add`
from picking up the local override; flipping it off
exposes the file again so a clean `git checkout` snaps
back to the committed state.

### Option B: Conda/Mamba (local dev only)

```bash
mamba env create --name gpf --file ./environment.yml
mamba env update --name gpf --file ./dev-environment.yml
conda activate gpf

pip install -e ../gain/core
pip install -e core
pip install -e web_api

# Optional extensions:
pip install -e federation
pip install -e rest_client
```

CI does not consume conda. Conda users can follow the
uv command shapes from inside an activated `gpf` env —
e.g. `pip install -e ./impala_storage` for the storage
backends, or running tests/lint without the `uv run`
prefix.

### Run tests

```bash
# Quick cycles
cd core
uv run pytest -v tests/small/test_file.py
uv run pytest -v tests/small/module/

# Full suites in parallel
cd core    && uv run pytest -v -n 10 tests/
cd web_api && uv run pytest -v -n 5 gpf_web/
```

Conda users: from inside an activated `gpf` env, drop the
`uv run` prefix (`pytest -v -n 10 tests/` directly).

Test markers and configuration are defined in
`core/pytest.ini` (e.g., `gs_inmemory`, `gs_duckdb`,
`gs_duckdb_parquet`, `grr_rw`, `grr_ro`, `grr_http`).

### Linting and type checking

```bash
uv run ruff check --fix .
uv run mypy gpf --exclude core/docs/
uv run mypy gpf_web --exclude web_api/docs/ \
    --exclude web_api/conftest.py
```

### Optional genotype storages

The optional storage backends (`gpf_impala_storage`,
`gpf_impala2_storage`, `gpf_gcp_storage`) bring in heavy
non-Python dependencies (Java/Hadoop, the Google Cloud
SDKs) that aren't on PyPI as wheels. They have their own
`pyproject.toml` files but are deliberately **not**
workspace members of the root coordinator — installing
all workspace members would otherwise pull these heavy
backend deps into the lockfile for everyone. Install
them standalone into the active venv:

```bash
uv pip install -e ./impala_storage
uv pip install -e ./impala2_storage
uv pip install -e ./gcp_storage
```

Conda users: use plain `pip install -e ./impala_storage`
(etc.) from inside the activated conda env — same shape.

GCP storage tests need application-default credentials for
the `seqpipe-gcp-storage-testing` project:

```bash
gcloud config list project
gcloud auth application-default login
```

Then, from the `gcp_storage/` directory:

```bash
uv run pytest -v gcp_storage/tests/
uv run pytest -v ../core/tests/ \
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

### Conda packaging

The `gpf-web` conda package bundles the Angular SPA so
`conda install gpf-web && wgpf` serves a fully working UI in
one process — handy for poking at newly imported studies
without a full split-mode docker deployment. CI assembles
the package automatically; to rebuild it locally for
testing, run the three-step:

```bash
# 1. Build the gpf-web wheel (same as for any other conda
#    recipe in this repo).
cd web_api && uv build --package gpf-web --out-dir ../dist/web_api && cd ..

# 2. Build the conda-flavoured SPA tarball. --base-href /
#    --deploy-url match the URL layout the Django gpfjs app
#    expects (STATIC_URL='/static/', index served at
#    /gpfjs/). environment.conda.ts is swapped in by
#    angular.json's `conda` configuration.
cd web_ui
npm ci
npm run build -- --configuration conda \
    --base-href '/gpfjs/' \
    --deploy-url '/static/gpfjs/gpfjs/'
mkdir -p ../dist/web_ui
tar -czf ../dist/web_ui/gpfjs-spa.tar.gz -C dist gpfjs
cd ..

# 3. Build the conda package.
rattler-build build \
    --recipe web_api/conda-recipe/recipe.yaml \
    --output-dir conda/web_api
```

The recipe in `web_api/conda-recipe/recipe.yaml` lists the
SPA tarball as a required source; rattler-build fails fast
if step 2 was skipped. The other three recipes (`core`,
`federation`, `rest_client`) don't need the SPA and can
build standalone with just step 1 + 3.

The released wheel itself stays SPA-free — the bundle is
conda-only. Production deploys consume the same wheel via
`web_api/Dockerfile.production` and pair it with the
apache-served `gpf-web-ui` image, so duplicating the SPA in
the wheel would just inflate the production backend image.

## Common pitfalls

- Prefer `uv run <cmd>` over activating the venv — works
  in any fresh shell without state.
- After `git pull`, re-run `uv sync --find-links
  ./dist/gain` (add `--all-packages --all-groups` if
  you've installed the optional workspace members) to
  pick up lockfile updates.
- After `git pull` in `../gain/`, rebuild the gain wheel
  and re-sync: `cd ../gain && uv build --package gain-core
  --out-dir ../gpf/dist/gain && cd ../gpf && uv sync
  --find-links ./dist/gain`. Editable-gain users skip this
  — see "Editable gain for local development" above.
- Conda users: always activate the `gpf` environment
  before running commands (`conda activate gpf`), and
  re-run `pip install -e core` if imports fail.
- Some tests may be flaky with high parallelism; reduce
  `-n` or run without it.

## License

This project is licensed under the MIT License. See
`LICENSE` for details.
