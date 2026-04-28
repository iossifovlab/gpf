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
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.11.3 /uv /uvx /usr/local/bin/

# System deps for building wheels that have no prebuilt Python 3.12 binaries
# (notably pyBigWig: needs gcc + libcurl).
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

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --package gpf-core --group dev --frozen --no-install-project

COPY core/ ./core/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --package gpf-core --group dev --frozen

ENV PATH="/workspace/.venv/bin:$PATH"
WORKDIR /workspace/core

CMD ["pytest", "-v", "-n", "auto", "tests/small/"]
