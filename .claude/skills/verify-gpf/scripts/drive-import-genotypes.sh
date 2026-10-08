#!/usr/bin/env bash
# drive-import-genotypes.sh <run id>
#
# Drive features/import-genotypes.md: import a de novo study of two trio
# families into the run's scratch instance through the checkout's
# .venv/bin/import_genotypes. Then dump the study with dump_study.py, a
# separate process that reads the instance back, and check the dump with
# readback-import-genotypes.sh.
#
# Evidence lands in .verify/<run id>/evidence/import-genotypes/:
#   command.txt  stdout.txt  stderr.txt  exit_code.txt
#   input.ped  input.tsv  import_project.yaml       the drive's inputs
#   study.yaml  storage_files.txt                   what the import wrote
#   variants.tsv  dump_stderr.txt  dump_exit_code.txt   the dump
#   readback.txt  readback_exit_code.txt
# Exits 0 only when import_genotypes exits 0, the dump exits 0 and the
# read-back passes.

source "$(dirname "${BASH_SOURCE[0]}")/app.sh"

run_dir="$(verify_run_dir "${1:-}")"
scratch="$run_dir/scratch"
instance="$(app_instance_dir "$scratch")"
evidence="$run_dir/evidence/import-genotypes"
[[ -f "$instance/gpf_instance.yaml" ]] \
    || verify_die "drive: $instance/gpf_instance.yaml is missing (run launch.sh)"
[[ ! -e "$evidence" ]] || verify_die "drive: $evidence already exists; launch a new run"
[[ ! -e "$instance/studies/$APP_STUDY_ID" ]] \
    || verify_die "drive: the run's instance already has $APP_STUDY_ID; launch a new run"
mkdir -p "$evidence" "$scratch/input"

# Two trio families. The genome is chrA, 100 x A, so each reference allele
# is A; the positions and the alternative alleles all differ, so a dropped,
# moved or swapped variant cannot pass the read-back.
printf '%s\n' \
    $'familyId\tpersonId\tdadId\tmomId\tsex\tstatus\trole' \
    $'f1\tf1.mom\t0\t0\t2\t1\tmom' \
    $'f1\tf1.dad\t0\t0\t1\t1\tdad' \
    $'f1\tf1.p1\tf1.dad\tf1.mom\t1\t2\tprb' \
    $'f2\tf2.mom\t0\t0\t2\t1\tmom' \
    $'f2\tf2.dad\t0\t0\t1\t1\tdad' \
    $'f2\tf2.p1\tf2.dad\tf2.mom\t2\t2\tprb' \
    > "$scratch/input/study.ped"
printf '%s\n' \
    $'familyId\tlocation\tvariant\tbestState' \
    $'f1\tchrA:11\tsub(A->C)\t2 2 1/0 0 1' \
    $'f1\tchrA:23\tsub(A->G)\t2 2 1/0 0 1' \
    $'f2\tchrA:37\tsub(A->T)\t2 2 1/0 0 1' \
    > "$scratch/input/study.tsv"
cat > "$scratch/input/import_project.yaml" <<YAML
id: $APP_STUDY_ID

input:
  input_dir: $(app_yaml_quote "$scratch/input")
  pedigree:
    file: study.ped
  denovo:
    files:
      - study.tsv
    location: location
    variant: variant
    family_id: familyId
    best_state: bestState

processing_config:
  work_dir: $(app_yaml_quote "$scratch/work")

destination:
  storage_id: verify_duckdb
YAML
cp "$scratch/input/study.ped" "$evidence/input.ped"
cp "$scratch/input/study.tsv" "$evidence/input.tsv"
cp "$scratch/input/import_project.yaml" "$evidence/import_project.yaml"

verify_drive "$scratch" "$evidence" \
    "$APP_VENV_BIN/import_genotypes" -i "$instance/gpf_instance.yaml" -j 1 \
    "$scratch/input/import_project.yaml"
study_yaml="$instance/studies/$APP_STUDY_ID/$APP_STUDY_ID.yaml"
[[ -f "$study_yaml" ]] && cp "$study_yaml" "$evidence/study.yaml"
if [[ -d "$instance/genotype_storage/$APP_STUDY_ID" ]]; then
    (cd "$instance/genotype_storage" && find "$APP_STUDY_ID" -type f | sort) \
        > "$evidence/storage_files.txt"
fi
if [[ "$VERIFY_RC" -ne 0 ]]; then
    tail -n 20 "$evidence/stderr.txt" >&2 || true
    verify_die "drive: import_genotypes exited $VERIFY_RC; evidence in $evidence; run doctor.sh"
fi
[[ -f "$evidence/study.yaml" ]] \
    || verify_die "drive: import_genotypes exited 0 but wrote no $study_yaml"

# Second, independent read: a separate process builds the instance and
# queries the study. Its dump is the file the read-back checks.
dump_rc=0
(cd "$scratch" && verify_isolated "$scratch" \
    "$APP_VENV_BIN/python" -I "$VERIFY_SCRIPTS/dump_study.py" \
    "$instance/gpf_instance.yaml" "$APP_STUDY_ID") \
    > "$evidence/variants.tsv" 2> "$evidence/dump_stderr.txt" || dump_rc=$?
echo "$dump_rc" > "$evidence/dump_exit_code.txt"
[[ "$dump_rc" -eq 0 ]] \
    || verify_die "drive: dump_study.py exited $dump_rc; see $evidence/dump_stderr.txt"

verify_readback "$evidence" "$VERIFY_SCRIPTS/readback-import-genotypes.sh" "$evidence/variants.tsv"
echo "drive: PASS: evidence in $evidence"
