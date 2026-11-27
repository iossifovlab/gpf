# CI image for `gpf-core`.
#
# Build from the repo root so the workspace manifests and uv.lock are in the
# build context:
#     docker build -f core/Dockerfile -t gpf-core-ci .
#
# Default CMD runs the test suite. Override for linters:
#     docker run --rm gpf-core-ci ruff check core/
#     docker run --rm gpf-core-ci mypy gpf

# syntax=docker/dockerfile:1.7
ARG PYTHON_IMAGE=python:3.13-slim
FROM ${PYTHON_IMAGE}

COPY --from=ghcr.io/astral-sh/uv:0.11.3 /uv /uvx /usr/local/bin/

# System deps for building wheels that have no prebuilt binaries for the
# PYTHON_IMAGE interpreter (notably pyBigWig: needs gcc + libcurl).
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libcurl4-openssl-dev \
        git \
    && rm -rf /var/lib/apt/lists/*

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONHASHSEED=0

# crapper computes the CRAP table that the core stage of the root
# Jenkinsfile archives (#1187). mutator is for the mutation job of
# #1190. They are CI tools, not dependencies of any member: a pyproject
# entry would flow into the files that scripts/conda_env.py renders.
# `uv tool install` puts both in one tool environment, `mutator`, which
# no `uv sync` below touches. mutator imports crapper from that
# environment, so the image holds one crapper.
# `--with-executables-from` also puts the `crapper` command on PATH.
# The layer sits before every COPY of the workspace sources, so a source
# change keeps it cached.
# crapper downloads its tree-sitter grammar on first use, so the build
# fetches the Python grammar here and the CI run needs no download. The
# grammar lives in the tool environment, so its Python fetches it.
# CRAPPER_REV and MUTATOR_REV are the values of gain/core/Dockerfile.
# The `command -v` checks fail this RUN when the install puts no
# `mutator` or no `crapper` on PATH. A failed install or grammar fetch
# fails this RUN on purpose: Docker caches no failed layer, so the next
# build retries the install. A fallback such as `|| echo` would cache a
# layer without crapper, and every later build would archive an empty
# CRAP table. At run time the CRAP report never changes the build result.
ARG CRAPPER_REV=6fd92c4c9bcc56efb64a2f8743d5a2993bcfd42d
ARG MUTATOR_REV=a5a0cb803b66e0cdb8bf471b3b08af701d424a41
ENV UV_TOOL_DIR=/opt/uv-tools \
    UV_TOOL_BIN_DIR=/usr/local/bin
RUN --mount=type=cache,target=/root/.cache/uv \
    uv tool install "mutator @ git+https://github.com/unclebob/mutator@${MUTATOR_REV}" \
        --with-executables-from "crapper @ git+https://github.com/unclebob/crapper@${CRAPPER_REV}" \
    && command -v mutator && command -v crapper \
    && /opt/uv-tools/mutator/bin/python -c \
        "from tree_sitter_language_pack import download; download(['python'])"

WORKDIR /workspace

# Workspace manifests first — maximises layer cache hits when only source
# changes. README.md files are required by hatchling's metadata validation
# (the `readme = "README.md"` field in each pyproject.toml).
COPY pyproject.toml uv.lock ruff.toml mypy.ini pylintrc ./
COPY core/pyproject.toml core/README.md ./core/
COPY web_api/pyproject.toml web_api/README.md ./web_api/
COPY federation/pyproject.toml ./federation/
COPY rest_client/pyproject.toml rest_client/README.md ./rest_client/

# gain-core wheel: provided by the parent Jenkinsfile's `Fetch gain
# wheel` stage (copyArtifacts from gain master's last successful build)
# into dist/gain/. Wheel filename encodes the gain SHA via hatch-vcs,
# so a moving gain master invalidates this COPY layer by content — no
# docker-layer-cache stale-clone footgun (tb-eqh phase-5). Local devs:
# `cd ../gain && uv build --package gain-core --out-dir ../gpf/dist/gain`.
COPY dist/gain/ ./dist/gain/

# The gain master wheel has a pre-release version, for example
# 2026.11.1.post1.dev23+g<sha>. Without `--prerelease allow`, uv skips it
# and installs the latest gain release from PyPI instead. The other
# packages keep their locked versions: `--upgrade-package` frees only
# gain-core.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --package gpf-core --group dev --upgrade-package gain-core --find-links ./dist/gain --prerelease allow --no-install-project

COPY core/ ./core/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --package gpf-core --group dev --upgrade-package gain-core --find-links ./dist/gain --prerelease allow

# tests/small/test_conda_deps.py holds the committed environment files to
# a fresh render of the pyprojects copied above, and each conda recipe's
# run list to its pyproject (core's recipe arrives with core/ above); it
# hard-fails when any of them is missing.
# tests/small/test_gain_core_conda_probe.py runs
# scripts/gain_core_conda_probe.sh and hard-fails when it is missing.
# tests/small/test_gain_core_pin_freshness.py runs
# scripts/gain_core_pin_freshness.sh and hard-fails when it is missing.
# tests/small/test_mypy_guides_match_jenkinsfile.py holds the mypy
# commands in CLAUDE.md and README.md to the mypyTarget values in the
# Jenkinsfile and hard-fails when any of the three files is missing.
COPY environment.yml dev-environment.yml ./
COPY scripts/conda_env.py ./scripts/
COPY scripts/gain_core_conda_probe.sh ./scripts/
COPY scripts/gain_core_pin_freshness.sh ./scripts/
# The crapStep text of the core stage runs scripts/crap_report_html.py,
# and tests/small/test_crap_report_html.py and
# tests/small/test_crap_churn.py fail when it is missing (#1187).
COPY scripts/crap_report_html.py ./scripts/
COPY Jenkinsfile CLAUDE.md README.md ./
COPY web_api/conda-recipe/recipe.yaml ./web_api/conda-recipe/
COPY federation/conda-recipe/recipe.yaml ./federation/conda-recipe/
COPY rest_client/conda-recipe/recipe.yaml ./rest_client/conda-recipe/

ENV PATH="/workspace/.venv/bin:$PATH"
WORKDIR /workspace/core

CMD ["pytest", "-v", "-n", "auto", "tests/small/"]
