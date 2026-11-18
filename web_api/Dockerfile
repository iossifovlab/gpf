# CI image for `gpf-web`.
#
# Build from the repo root so the workspace manifests and uv.lock are in the
# build context:
#     docker build -f web_api/Dockerfile -t gpf-web-ci .
#
# Default CMD runs the test suite. Override for linters:
#     docker run --rm gpf-web-ci ruff check web_api/
#     docker run --rm gpf-web-ci mypy gpf_web

# syntax=docker/dockerfile:1.7
ARG PYTHON_IMAGE=python:3.13-slim
FROM ${PYTHON_IMAGE}

COPY --from=ghcr.io/astral-sh/uv:0.11.3 /uv /uvx /usr/local/bin/

# Build deps for transitive wheels (pyBigWig from gain-core needs gcc +
# libcurl).
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libcurl4-openssl-dev \
        git \
    && rm -rf /var/lib/apt/lists/*

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONHASHSEED=0

WORKDIR /workspace

# Workspace manifests first — maximises layer cache hits when only source
# changes. README.md files are required by hatchling's metadata validation
# (the `readme = "README.md"` field in each pyproject.toml).
COPY pyproject.toml uv.lock ruff.toml mypy.ini pylintrc ./
COPY core/pyproject.toml core/README.md ./core/
COPY web_api/pyproject.toml web_api/README.md ./web_api/
COPY federation/pyproject.toml ./federation/
COPY rest_client/pyproject.toml rest_client/README.md ./rest_client/

# gpf-core is a runtime dependency of gpf-web (via the GPFInstance plugin
# entry point). Copy its source so uv sync can install it editable.
COPY core/gpf/ ./core/gpf/

# gain-core wheel: provided by the parent Jenkinsfile's `Fetch gain
# wheel` stage (copyArtifacts from gain master's last successful build)
# into dist/gain/. Wheel filename encodes the gain SHA, so a moving
# gain master invalidates this COPY layer by content — no
# docker-layer-cache stale-clone footgun (tb-eqh phase-5). Local devs:
# `cd ../gain && uv build --package gain-core --out-dir ../gpf/dist/gain`.
COPY dist/gain/ ./dist/gain/

# The gain master wheel has a pre-release version, for example
# 2026.11.1.post1.dev23+g<sha>. Without `--prerelease allow`, uv skips it
# and installs the latest gain release from PyPI instead. The other
# packages keep their locked versions: `--upgrade-package` frees only
# gain-core.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --package gpf-web --group dev --upgrade-package gain-core --find-links ./dist/gain --prerelease allow --no-install-project

COPY web_api/ ./web_api/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --package gpf-web --group dev --upgrade-package gain-core --find-links ./dist/gain --prerelease allow

ENV PATH="/workspace/.venv/bin:$PATH"
WORKDIR /workspace/web_api

CMD ["pytest", "-v", "gpf_web/"]
