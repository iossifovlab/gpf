#!/usr/bin/env bash
# cleanup.sh <run id>
#
# Remove .verify/<run id>/scratch/ (the GRR copy, the instance, the inputs
# and the work directory) and keep .verify/<run id>/evidence/. verify-gpf
# starts no containers, so there is no compose project to bring down.

source "$(dirname "${BASH_SOURCE[0]}")/app.sh"

run_dir="$(verify_run_dir "${1:-}")"
rm -rf -- "$run_dir/scratch"
echo "cleanup: removed $run_dir/scratch; evidence kept in $run_dir/evidence"
