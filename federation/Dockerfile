# CI image for `gpf-federation`.
#
# Build from the repo root so the workspace manifests and uv.lock are in the
# build context:
#     docker build -f federation/Dockerfile -t gpf-federation-ci .
#
# Default CMD runs the test suite.

# syntax=docker/dockerfile:1.7
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.11.3 /uv /uvx /usr/local/bin/

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libcurl4-openssl-dev \
        git \
    && rm -rf /var/lib/apt/lists/*

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONHASHSEED=0

ARG GAIN_REVISION=master
RUN git clone https://github.com/iossifovlab/gain.git /gain \
    && git -C /gain checkout ${GAIN_REVISION}

WORKDIR /workspace

COPY pyproject.toml uv.lock ruff.toml mypy.ini pylintrc ./
COPY core/pyproject.toml ./core/
COPY web/pyproject.toml ./web/
COPY federation/pyproject.toml ./federation/
COPY rest_client/pyproject.toml ./rest_client/

# Federation depends on gpf-core + gpf-web; copy their sources so uv sync can
# install them editable.
COPY core/gpf/ ./core/gpf/
COPY web/gpf_web/ ./web/gpf_web/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --package gpf-federation --group dev --frozen --no-install-project

COPY federation/ ./federation/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --package gpf-federation --group dev --frozen

ENV PATH="/workspace/.venv/bin:$PATH"
WORKDIR /workspace/federation

CMD ["pytest", "-v", "tests/"]
