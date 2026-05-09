# CI image used by the Jenkins pipeline to build conda packages
# (rattler-build) and Python wheels/sdists (`uv build`) for every
# sub-project, plus push them to Anaconda.org (anaconda-client).
# `git` is also installed because hatch-vcs derives the embedded
# PEP 440 version from the git tree.
#
# Usage:
#   docker build -f conda-builder/Dockerfile -t gpf-conda-builder-ci .
#   docker run --rm \
#       -v $PWD:/workspace \
#       -w /workspace \
#       gpf-conda-builder-ci \
#       rattler-build build --recipe core/conda-recipe/recipe.yaml \
#           --output-dir conda/core

# syntax=docker/dockerfile:1.7
FROM mambaorg/micromamba:2.3.2

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        git \
    && rm -rf /var/lib/apt/lists/*

USER mambauser
# anaconda-client provides `anaconda upload`, used by the
# tag-driven release pipeline to publish .conda packages to the
# iossifovlab org on Anaconda.org. uv builds the wheels/sdists
# in the same pipeline. Same image, no PATH change
# (/opt/conda/bin is already on PATH below).
RUN micromamba install -n base -y -c conda-forge \
        rattler-build anaconda-client uv \
    && micromamba clean --all --yes

# Make the rattler-build binary callable directly without `micromamba run`.
ENV PATH="/opt/conda/bin:$PATH"

WORKDIR /workspace
