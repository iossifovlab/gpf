# shellcheck shell=bash
# The gpf code of the verify-gpf scripts. Sourced, not executed. The
# launch, drive, doctor and cleanup scripts source this file only; the
# readback-*.sh scripts are standalone. It sources verify-lib.sh, the copy
# of the canonical contract code (do not edit that copy).

# shellcheck disable=SC2034  # read by verify-lib.sh
VERIFY_APP=gpf
# shellcheck source=verify-lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/verify-lib.sh"

# shellcheck disable=SC2034  # read by the scripts that source app.sh
APP_VENV_BIN="$VERIFY_CHECKOUT/.venv/bin"

# The committed fixture: a directory GRR with genomes/mock (chrA, 100 x A)
# and gene_models/mock (no genes). VERIFY_GPF_FIXTURE_GRR overrides it, so
# the missing-fixture failure of doctor.sh can be proved without touching
# the checkout.
# shellcheck disable=SC2034  # read by the scripts that source app.sh
APP_FIXTURE_GRR="${VERIFY_GPF_FIXTURE_GRR:-$VERIFY_CHECKOUT/core/tests/small/tools/fixtures/repo}"

# The id of the study that the import-genotypes drive imports.
# shellcheck disable=SC2034  # read by the drive and doctor scripts
APP_STUDY_ID=verify_study

# app_instance_dir <scratch dir> -> prints the run's GPF instance directory.
app_instance_dir() {
    echo "$1/instance"
}

# app_env <scratch dir>: called by verify_isolated_env. Append the gpf
# entries to VERIFY_ENV, so a drive and its command.txt use the same ones:
#   - GRR_DEFINITION_FILE pointing at the run's directory-GRR definition
#     over the scratch copy of the fixture (HOME is inside scratch too, so
#     ~/.grr_definition.yaml is never read, and no GRR request leaves the
#     host);
#   - DAE_DB_DIR pointing at the run's scratch instance, so a DAE_DB_DIR in
#     the caller's environment never names a real instance.
app_env() {
    local scratch="$1"
    VERIFY_ENV+=(
        GRR_DEFINITION_FILE="$scratch/grr.yaml"
        DAE_DB_DIR="$(app_instance_dir "$scratch")"
    )
}

# app_yaml_quote <string> -> prints the string as a YAML single-quoted
# scalar (embedded ' doubled), so a checkout path holding ': ', ' #' or a
# leading indicator character stays one value.
app_yaml_quote() {
    local q="'"
    printf "'%s'" "${1//$q/$q$q}"
}

# app_check_cli <tool>: fails, naming the fix, unless the <tool> on PATH is
# this checkout's .venv/bin/<tool>. A conda env or another worktree's venv
# can shadow it.
app_check_cli() {
    local tool="$1" found
    [[ -x "$APP_VENV_BIN/$tool" ]] \
        || verify_die "FAIL: $APP_VENV_BIN/$tool is missing.
    Fix: build the gain wheel into dist/gain and run uv sync (see features/README.md)."
    found="$(command -v "$tool" || true)"
    [[ "$found" == "$APP_VENV_BIN/$tool" ]] \
        || verify_die "FAIL: $tool on PATH is '${found:-nothing}', not this checkout's $APP_VENV_BIN/$tool.
    Fix: export PATH=\"$APP_VENV_BIN:\$PATH\""
}

# app_check_imports: fails unless the .venv python imports gpf from this
# checkout's core/gpf (an editable install of another checkout would test
# the wrong source) and imports gain from this .venv.
app_check_imports() {
    local paths gpf_dir gain_dir
    paths="$("$APP_VENV_BIN/python" -I -c 'import os, gpf, gain
print(os.path.dirname(gpf.__file__))
print(os.path.dirname(gain.__file__))' 2>&1)" \
        || verify_die "FAIL: $APP_VENV_BIN/python cannot import gpf and gain:
$paths
    Fix: build the gain wheel from gain master into dist/gain and run uv sync (see features/README.md)."
    gpf_dir="$(sed -n 1p <<< "$paths")"
    gain_dir="$(sed -n 2p <<< "$paths")"
    [[ "$gpf_dir" == "$VERIFY_CHECKOUT/core/gpf" ]] \
        || verify_die "FAIL: gpf imports from $gpf_dir, not $VERIFY_CHECKOUT/core/gpf.
    Fix: run uv sync in this checkout."
    [[ "$gain_dir" == "$VERIFY_CHECKOUT/.venv/"* ]] \
        || verify_die "FAIL: gain imports from $gain_dir, not from $VERIFY_CHECKOUT/.venv.
    Fix: run uv sync in this checkout."
}
