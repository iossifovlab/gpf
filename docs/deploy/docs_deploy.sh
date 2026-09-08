#!/usr/bin/env bash
# Ship docs/gpfdocs-html.tar.gz to the iossifovlab.com docs host.
# Run from the gpf repo root after `docs/build_docs.sh` has produced
# the tarball:
#     bash docs/deploy/docs_deploy.sh
#
# Set DOCS_STAMP to name the release directory the play publishes; see
# `docs_stamp` in docs_deploy.yaml, which reads it from the environment.
# CI sets it to "<build number>-<short sha>"; without it the release is
# named after the clock.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "${REPO_ROOT}/docs/deploy"

ansible-playbook -i docs_inventory docs_deploy.yaml
