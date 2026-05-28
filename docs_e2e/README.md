# docs-e2e

Guide-accuracy regression for the [GPF Getting Started
Guide][published-guide]. Drives the guide's setup → import → query
flow as written, against the freshly-built `gpf-web` conda
package, and asserts each prose claim. Failures cite the RST
file:line so drift surfaces directly to the line that needs
updating (or to the regression that broke the claim).

See the parent epic [iossifovlab/gpf#871][epic] and the v1 issue
[iossifovlab/gpf#872][v1-issue] for the full design.

[published-guide]: https://iossifovlab.com/gpfdocs/administration/getting_started/getting_started.html
[epic]: https://github.com/iossifovlab/gpf/issues/871
[v1-issue]: https://github.com/iossifovlab/gpf/issues/872

## How the build works

Per build:

1. **Test driver image** — `docs_e2e/Dockerfile` (base:
   `condaforge/miniforge3`) starts with `pytest + httpx` in a
   tiny `driver` mamba env.
2. **Install** — the `gpf_env_prefix` conftest fixture creates a
   *fresh* gpf-web env from this build's `dist/conda/*.conda`
   artefacts (mounted at `/workspace/dist/conda`), layered on
   the upstream `iossifovlab`/`bioconda`/`conda-forge` channels.
   Mirrors what `mamba install gpf-web` does for an end user.
3. **Clone demo data** — `getting_started_clone` fixture
   shallow-clones `iossifovlab/gpf-getting-started` master.
   Same source `docs/build_docs.sh` uses.
4. **GRR cache** — Jenkinsfile mounts the persistent
   `gpf-grr-cache` docker volume into the container. First
   build on a fresh agent demand-pulls hg38 (~3 GB, ~10 min);
   subsequent builds reuse the cache.
5. **Run guide** — pytest tests execute the guide's commands
   verbatim (`import_genotypes input_genotype_data/denovo_example.yaml`,
   etc.), then bring up `wgpf run` in a background subprocess
   and assert each prose claim through `guide_assertions`
   helpers.

## Strict mode

Tests run **only** what the guide tells users to run. No silent
`wdaemanage migrate` or user-create in conftest. If `wgpf run`
against an empty `$DAE_DB_DIR` requires those steps, the fix is
to update the guide — not to add hidden setup in conftest.

The line: would a real user, following the guide, type this?

* **Yes** → it goes in a test, exercised via subprocess.
* **No, but it's invisible infrastructure (GRR cache volume, local
  channel mount, the test driver image itself)** → it goes in
  conftest or the Dockerfile.

Anything else is drift, not infrastructure. Fix the guide.

## Local iteration

You need the same artefacts CI uses: a directory of
`gpf-web-*.conda` files. Easiest path is to copy them from a
recent green CI build. Then:

```bash
# From the gpf repo root, with dist/conda/ populated:
docker build -f docs_e2e/Dockerfile -t gpf-docs-e2e:dev .

docker run --rm \
    -v "$PWD:/workspace" \
    -v gpf-grr-cache:/grr-cache \
    -e DOCS_E2E_CHANNEL=/workspace/dist/conda \
    -e DOCS_E2E_GRR_CACHE=/grr-cache \
    gpf-docs-e2e:dev
```

To iterate on a single test:

```bash
docker run --rm \
    -v "$PWD:/workspace" \
    -v gpf-grr-cache:/grr-cache \
    -e DOCS_E2E_CHANNEL=/workspace/dist/conda \
    -e DOCS_E2E_GRR_CACHE=/grr-cache \
    gpf-docs-e2e:dev \
    mamba run -n driver \
        pytest -v docs_e2e/tests/test_main_body.py::TestDenovoImport
```

The `guide_assertions` unit tests don't need conda or wgpf:

```bash
.venv/bin/python -m pytest docs_e2e/test_guide_assertions.py
```

These run as part of gpf-core CI (pure Python; ~0.04s).

## Adding a new sub-guide stage

The phased rollout (#871) splits each `.. include::`'d sub-guide
into its own follow-up issue. To onboard one:

1. Create `docs_e2e/tests/test_<name>.py`.
2. Write one test per discrete claim in the sub-guide RST. Use
   `guide_assertions` helpers — add new ones only when a
   genuinely new assertion shape appears.
3. Strict mode: if your tests fail because the guide is missing
   a step, the fix is to update the RST. Land both in the same PR.
4. Tick the child checkbox on epic #871.

No Jenkinsfile changes are needed — pytest collects all
`tests/test_*.py` automatically.

## Layout

```
docs_e2e/
├── Dockerfile               # test driver image (miniforge + pytest + httpx)
├── README.md                # this file
├── Jenkinsfile.docs-e2e     # downstream pipeline
├── jenkins-jobs/
│   └── docs_e2e.groovy      # pipelineJob DSL, seeded by main gpf Jenkinsfile
├── conftest.py              # fixtures: conda_channel, gpf_env_prefix, getting_started_clone, prepared_instance, annotated_instance, wgpf_server
├── guide_assertions.py      # deep module — uniform failure-message helpers
├── test_guide_assertions.py # unit tests for the module (pure Python)
├── __init__.py
└── tests/
    ├── __init__.py
    ├── test_main_body.py    # v1: main getting_started.rst body claims
    └── test_annotation.py   # getting_started_with_annotation.rst claims
```
