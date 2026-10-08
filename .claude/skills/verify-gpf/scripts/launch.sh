#!/usr/bin/env bash
# launch.sh [run id]
#
# Create .verify/<run id>/scratch/ and .verify/<run id>/evidence/ in the
# checkout, then build the run's GPF instance in scratch:
#   scratch/grr/                          a copy of the committed fixture GRR
#   scratch/grr.yaml                      a directory GRR over that copy
#   scratch/instance/gpf_instance.yaml    genomes/mock, gene_models/mock and
#                                         a duckdb_parquet genotype storage
#                                         under scratch/instance/
# The fixture in the checkout is never written. Prints the run id on stdout
# (the last line). ~/.grr_definition.yaml is neither read nor changed.

source "$(dirname "${BASH_SOURCE[0]}")/app.sh"

run_id="${1-$(date +%Y%m%d-%H%M%S)-$$}"
verify_check_run_id "$run_id"
run_dir="$VERIFY_ROOT/$run_id"
[[ ! -e "$run_dir" ]] || verify_die "run $run_dir already exists; pick another run id"
[[ -f "$APP_FIXTURE_GRR/genomes/mock/genomic_resource.yaml" ]] \
    || verify_die "the fixture GRR $APP_FIXTURE_GRR has no genomes/mock (run doctor.sh)"

scratch="$run_dir/scratch"
instance="$(app_instance_dir "$scratch")"
mkdir -p "$scratch" "$run_dir/evidence" "$instance"

cp -R "$APP_FIXTURE_GRR" "$scratch/grr"
cat > "$scratch/grr.yaml" <<YAML
id: fixture
type: directory
directory: $(app_yaml_quote "$scratch/grr")
YAML

# No annotation: the fixture's annotation.yaml names scores/mock1 and
# scores/mock2, whose data files are placeholders that cannot annotate.
# %(wd)s is the directory of gpf_instance.yaml, so the storage stays in
# scratch.
cat > "$instance/gpf_instance.yaml" <<'YAML'
instance_id: verify_gpf

reference_genome:
  resource_id: genomes/mock

gene_models:
  resource_id: gene_models/mock

genotype_storage:
  default: verify_duckdb
  storages:
    - id: verify_duckdb
      storage_type: duckdb_parquet
      base_dir: "%(wd)s/genotype_storage"
YAML

echo "verify-gpf: launched run at $run_dir" >&2
echo "$run_id"
