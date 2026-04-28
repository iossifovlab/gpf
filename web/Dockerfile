# CI image for `gpf-web`.
#
# Build from the repo root so the workspace manifests and uv.lock are in the
# build context:
#     docker build -f web/Dockerfile -t gpf-web-ci .
#
# Default CMD runs the test suite. Override for linters:
#     docker run --rm gpf-web-ci ruff check web/
#     docker run --rm gpf-web-ci mypy gpf_web

# syntax=docker/dockerfile:1.7
FROM python:3.12-slim

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

# gain lives in a sibling repo — clone it into /gain so the path
# in [tool.uv.sources] (`../gain/core` relative to the gpf workspace
# root at /workspace) resolves correctly.
ARG GAIN_REVISION=master
RUN git clone https://github.com/iossifovlab/gain.git /gain \
    && git -C /gain checkout ${GAIN_REVISION}

WORKDIR /workspace

# Workspace manifests first — maximises layer cache hits when only source
# changes.
COPY pyproject.toml uv.lock ruff.toml mypy.ini pylintrc ./
COPY core/pyproject.toml ./core/
COPY web/pyproject.toml ./web/
COPY federation/pyproject.toml ./federation/
COPY rest_client/pyproject.toml ./rest_client/

# gpf-core is a runtime dependency of gpf-web (via the GPFInstance plugin
# entry point). Copy its source so uv sync can install it editable.
COPY core/gpf/ ./core/gpf/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --package gpf-web --group dev --frozen --no-install-project

COPY web/ ./web/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --package gpf-web --group dev --frozen

ENV PATH="/workspace/.venv/bin:$PATH"
WORKDIR /workspace/web

CMD ["pytest", "-v", "gpf_web/"]
