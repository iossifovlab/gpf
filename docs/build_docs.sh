#!/usr/bin/env bash
# Build the GPF Sphinx documentation tree.
#
# Run from the gpf repository root:
#     uv sync --group docs
#     uv run bash docs/build_docs.sh
#
# Produces:
#     docs/build/html/         rendered site
#     docs/gpfdocs-html.tar.gz tarball consumed by docs/deploy/
#
# In CI, the Build docs Jenkinsfile stage only runs when the
# `docs/**` tree changes (see `when { changeset 'docs/**' }` in
# Jenkinsfile). Edits outside docs/ do not refresh the rendered
# autodoc page until a subsequent docs-tree commit lands.
#
# The Deploy docs stage authenticates to iossifovlab.com via the
# `gpf-docs-deploy` Jenkins-managed SSH credential.

set -euo pipefail

# Repo root regardless of where the script is invoked from.
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${REPO_ROOT}"

# `docs/source/administration/getting_started/gpf-getting-started`
# is a symlink to <repo-root>/gpf-getting-started — `literalinclude`
# directives in the rst pull example pedigrees / configs from it.
# Clone it on demand (gitignored).
if [ ! -d "gpf-getting-started" ]; then
    git clone --depth 1 \
        https://github.com/iossifovlab/gpf-getting-started.git \
        gpf-getting-started
fi

# autodoc imports gpf_web Django apps, which requires migrations
# to have run against *some* GPF instance. Stand up a throwaway
# hg38_hello instance pointed at the public grr and migrate.
INSTANCE_DIR="${REPO_ROOT}/docs/.tmp/instance"
mkdir -p "${INSTANCE_DIR}"
cat > "${INSTANCE_DIR}/gpf_instance.yaml" << 'EOT'
instance_id: "hg38_hello"

reference_genome:
    resource_id: "hg38/genomes/GRCh38-hg38"

gene_models:
    resource_id: "hg38/gene_models/refSeq_v20200330"
EOT

CACHE_DIR="${REPO_ROOT}/docs/.tmp/cache"
mkdir -p "${CACHE_DIR}"
cat > "${CACHE_DIR}/grr_definition.yaml" << EOT
id: "default"
type: "url"
url: "https://grr.seqpipe.org/"
cache_dir: "${CACHE_DIR}/grrCache"
EOT

export DAE_DB_DIR="${INSTANCE_DIR}"

wdaemanage migrate
wdaemanage user_create admin@iossifovlab.com -p secret \
    -g any_dataset:admin || true

# Clean previous auto-generated trees so stale modules don't
# linger if files were deleted upstream.
rm -rf docs/source/development/gpf
rm -rf docs/source/development/gpf_web

# sphinx-apidoc → .rst skeletons with automodule directives.
sphinx-apidoc -o docs/source/development/gpf/modules/ core/gpf
sphinx-apidoc -o docs/source/development/gpf_web/modules/ \
    web_api/gpf_web "*tests*"

# api_docs_generator → httpdomain routes for gpf_web REST views.
python docs/api_docs_generator.py \
    --root_dir web_api \
    --output_dir docs/source/development/gpf_web/routes

# Build HTML.
rm -rf docs/build
sphinx-build -M html docs/source docs/build

# Tarball for ansible deploy.
tar -czf docs/gpfdocs-html.tar.gz -C docs/build/ html/
