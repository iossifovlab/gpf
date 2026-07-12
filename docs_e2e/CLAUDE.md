# docs-e2e — Agent Guide

Guide-accuracy regression suite for the GPF Getting Started Guide
(epic iossifovlab/gpf#871). Each sub-guide RST has a
`tests/test_<name>.py` whose tests assert the guide's discrete prose
claims by running its commands and probing a backgrounded `wgpf run`.
Full design + local-iteration details: `docs_e2e/README.md`.

## ALWAYS run the suite locally before committing

The Jenkins `gpf-docs-e2e` build is **not** your first test. Almost the
entire suite is **session fixtures** (`conftest.py`) exercised only at
**runtime**, so `py_compile`, `ruff`, and even `pytest --collect-only`
do **not** catch the most common breakage: a fixture referenced by bare
name instead of being injected as a parameter. That fails at fixture
setup and cascades to **every** server-backed test as an ERROR (see
build #35: a stray `denovo_instance` in `wgpf_server` → 63 passed, 33
errors). Only actually running the suite catches it.

Emulate the Jenkins run in the driver container (needs docker,
`dist/conda/gpf-web-*.conda` **and** `dist/conda/gain-core-*.conda`
artefacts, and a populated `gpf-grr-cache` volume — see README § Local
iteration):

```bash
# from the gpf checkout, with dist/conda populated:
docker build -f docs_e2e/Dockerfile -t gpf-docs-e2e:local docs_e2e/
docker run --rm -v "$PWD:/workspace" -v gpf-grr-cache:/grr-cache \
    -e DOCS_E2E_CHANNEL=/workspace/dist/conda \
    -e DOCS_E2E_GRR_CACHE=/grr-cache -w /workspace \
    gpf-docs-e2e:local mamba run -n driver pytest -v -s docs_e2e/
```

- No local `dist/conda`? Reuse a sibling worktree's
  `dist/conda/*.conda` (any recent gpf build works — the GRR resources
  are version-independent), or pull from a gpf build.
- The install drops the `iossifovlab` channel (gpf#916), so the local
  `dist/conda` must **also** hold a `gain-core-*.conda` — the gpf build
  only produces `gpf-*`. In CI the `gpf-docs-e2e` Jenkinsfile copies it
  from gain master's last build; locally, drop a `gain-core-*.conda`
  (from a gain build, or `uv build`/`rattler-build` of `../gain`) into
  `dist/conda/` or the solve fails with `nothing provides gain-core`.
- Local `gpf-grr-cache` populated but missing the `.docs-e2e-prewarmed`
  sentinel? `touch` it once:
  `docker run --rm -v gpf-grr-cache:/grr-cache alpine touch /grr-cache/.docs-e2e-prewarmed`
- Iterating on one sub-guide? Running just its file still pulls the
  **whole** session-fixture chain (so it catches wiring breaks):
  `… pytest -v -s docs_e2e/tests/test_<name>.py`.

## Strict mode (#871)

Tests run **only** what the guide tells users to run — no silent
`migrate`, no hidden user creation, no quietly-pre-imported study. If a
step is missing, fix the **guide**, not the harness. The one sanctioned
exception is invisible infrastructure no real user sees (the local conda
channel, the persistent GRR cache). Documented data carve-outs (capping
an import to N variants for the time budget) are allowed **only** when
the guide's command still runs verbatim — see `_DENOVO_VARIANT_CAP` /
`_CNV_VARIANT_CAP` in `conftest.py` (issues #876 / #877). Every test
failure must carry the originating `RST file:line` (`rst_ref=`).

## Per-agent GRR cache seeding

The suite is pinned to one agent (`AGENT_LABEL`, default `pooh`) and
needs that agent's node-local `gpf-grr-cache` volume pre-seeded by the
`gpf-docs-e2e-prewarm` job (it bulk-caches ~15 GB of instance resources
out of band; the build then validates the warm cache fast). The
`grr_cache_seeded` conftest guard fails fast on an unseeded agent. The
prewarm currently uses `grr_cache_repo -j 1` to dodge a gain HTTP-timeout
bug (iossifovlab/gain#43) — drop back to `-j 4` once that's fixed.
