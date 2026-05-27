# docs-e2e test driver image.
#
# Base: condaforge/miniforge3 — matches what the published
# Getting Started Guide recommends users install, so the install
# path docs-e2e exercises is the same path a brand-new user walks.
# This is the whole point of (B) guide-accuracy regression: install
# from a clean Miniforge, not from gpf's heavy CI image.
#
# Two-env separation:
#   * "driver" env  — pytest + httpx, the test runner. Stable
#     across gpf changes; rebuilt only when docs_e2e itself adds
#     a Python dep.
#   * gpf_web env   — built at test time by conftest's
#     install_gpf_web fixture, using the .conda artefacts copied
#     from the upstream gpf build (mounted at
#     /workspace/dist/conda). This is the system-under-test.
#
# Keeping them separate means the driver is invariant — a regression
# in gpf_web's own python deps can break the SUT install without
# also breaking the test runner.

FROM condaforge/miniforge3:24.11.3-0

# git: shallow-clones iossifovlab/gpf-getting-started master in
#      the getting_started_clone fixture.
# curl: ad-hoc liveness probes from inside the container if needed
#      (the suite itself uses httpx).
# ca-certificates: HTTPS to grr.iossifovlab.com is GRR-cache miss
#      handled by the wgpf process itself, but git clone over https
#      needs them too.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        git \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Driver env. python-version 3.12 matches gpf-monorepo's
# requires-python so subprocess invocations of gpf-shipped CLIs
# from this env don't hit a Python-version mismatch (they run
# inside the gpf_web env anyway via `mamba run`, but a matching
# driver Python keeps anything we might in-process-import stable).
RUN mamba create -y -n driver python=3.12 \
    && mamba run -n driver pip install --no-cache-dir \
        pytest \
        pytest-timeout \
        httpx \
        pyyaml \
        conda-index \
    && mamba clean -afy

# conda-index above: the upstream gpf master archive ships
# `dist/conda/*.conda` as a flat directory of artefacts, not as a
# proper conda channel layout. mamba cannot install from it as
# `-c file://...` without `noarch/repodata.json`. The conftest's
# `conda_channel` fixture uses `python -m conda_index` to build
# that index in a tempdir before the install runs.

# The Jenkinsfile mounts the gpf workspace at /workspace and
# invokes pytest from there. Working dir set here so an ad-hoc
# `docker run` for local iteration lands in the right place.
WORKDIR /workspace

# Default cmd is the canonical local-run invocation. CI overrides
# with explicit pytest args.
CMD ["mamba", "run", "--no-capture-output", "-n", "driver", \
     "pytest", "-v", "docs_e2e/"]
