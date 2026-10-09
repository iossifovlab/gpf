#!/usr/bin/env bash
# doctor.sh <run id>
#
# Preflight. Writes nothing outside the run's scratch directory. Fails (exit 1) with a message that names the fix when:
#   1. import_genotypes on PATH is not this checkout's .venv/bin one;
#   2. the .venv python does not import gpf from this checkout's core/gpf,
#      or gain from this .venv;
#   3. the fixture GRR (core/tests/small/tools/fixtures/repo) lacks
#      genomes/mock or gene_models/mock;
#   4. the run's instance does not load: GPFInstance.build on
#      scratch/instance/gpf_instance.yaml, in the run's isolated
#      environment, must give the chrA reference genome of length 100.

source "$(dirname "${BASH_SOURCE[0]}")/app.sh"

run_dir="$(verify_run_dir "${1:-}")"
scratch="$run_dir/scratch"
instance="$(app_instance_dir "$scratch")"

# 1. The CLI the drive runs.
app_check_cli import_genotypes
echo "doctor: ok: import_genotypes is $APP_VENV_BIN/import_genotypes"

# 2. The source the CLI runs.
app_check_imports
echo "doctor: ok: gpf imports from $VERIFY_CHECKOUT/core/gpf, gain from the .venv"

# 3. The committed fixture.
for res in genomes/mock gene_models/mock; do
    [[ -f "$APP_FIXTURE_GRR/$res/genomic_resource.yaml" ]] \
        || verify_die "doctor: FAIL: $APP_FIXTURE_GRR/$res/genomic_resource.yaml is missing.
    Fix: restore core/tests/small/tools/fixtures/repo (git checkout -- core/tests/small/tools/fixtures/repo)."
done
echo "doctor: ok: fixture GRR $APP_FIXTURE_GRR has genomes/mock and gene_models/mock"

# 4. The run's instance.
[[ -f "$instance/gpf_instance.yaml" ]] \
    || verify_die "doctor: FAIL: $instance/gpf_instance.yaml is missing (run launch.sh)"
mkdir -p "$scratch/home" "$scratch/tmp"
probe="$(cd "$scratch" && verify_isolated "$scratch" "$APP_VENV_BIN/python" -I -c '
import sys
from gpf.gpf_instance import GPFInstance
inst = GPFInstance.build(sys.argv[1])
genome = inst.reference_genome
print(",".join(genome.chromosomes), genome.get_chrom_length("chrA"))
' "$instance/gpf_instance.yaml" 2> "$scratch/doctor-instance.err")" \
    || verify_die "doctor: FAIL: the run's instance does not load; see $scratch/doctor-instance.err"
[[ "$probe" == "chrA 100" ]] \
    || verify_die "doctor: FAIL: the run's reference genome is '$probe', not 'chrA 100'"
echo "doctor: ok: the run's instance loads genomes/mock (chrA, 100 bases)"

echo "doctor: PASS"
