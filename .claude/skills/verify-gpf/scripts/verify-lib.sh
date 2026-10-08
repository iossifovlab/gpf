# verify-lib.sh: copied from lchorbadjiev/skills engineering/create-verify-skill at d231c33. Do not edit this copy.
# shellcheck shell=bash
#
# The contract code of a verify-<app> skill. Sourced, not executed, by the
# skill's app.sh, which sets VERIFY_APP first. This file names no app: every
# app value comes from app.sh. The drift check of create-verify-skill
# compares everything below the first line with the canonical file.

set -euo pipefail

[[ -n "${VERIFY_APP:-}" ]] || {
    echo "verify-lib.sh: set VERIFY_APP in app.sh before sourcing verify-lib.sh" >&2
    exit 1
}

# verify_die <message>: print "verify-<app>: <message>" to stderr, exit 1.
verify_die() {
    echo "verify-$VERIFY_APP: $*" >&2
    exit 1
}

# The scripts directory holds this file. The checkout is the git worktree
# that holds the skill, and every run lives under its .verify/ directory.
VERIFY_SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
VERIFY_CHECKOUT="$(git -C "$VERIFY_SCRIPTS" rev-parse --show-toplevel)" \
    || verify_die "$VERIFY_SCRIPTS is not inside a git worktree"
VERIFY_ROOT="$VERIFY_CHECKOUT/.verify"

# verify_check_run_id <run id>: fail unless the id is a safe directory name
# and a valid docker compose project suffix. Compose takes only lowercase
# letters, digits, '-' and '_' in a project name. The rule for the first
# character rules out '.', '..', '-x' and '_x'.
verify_check_run_id() {
    [[ "${1:-}" =~ ^[a-z0-9][a-z0-9_-]*$ ]] \
        || verify_die "run id '${1:-}' is not valid: use lowercase letters, digits, '_' and '-', and start with a letter or a digit (it names the compose project verify-$VERIFY_APP-<run id>)"
}

# verify_run_dir <run id>: print the absolute path $VERIFY_ROOT/<run id>,
# fail unless it is a run.
verify_run_dir() {
    local run_id="${1:-}"
    [[ -n "$run_id" ]] || verify_die "missing <run id> argument"
    verify_check_run_id "$run_id"
    local run_dir="$VERIFY_ROOT/$run_id"
    [[ -d "$run_dir/evidence" ]] \
        || verify_die "no run at $run_dir (run launch.sh first)"
    echo "$run_dir"
}

# --- The isolated environment ----------------------------------------------

# verify_isolated_env <scratch dir>: set the array VERIFY_ENV to the
# NAME=value entries that a drive runs under. HOME, TMPDIR and the XDG
# directories are inside scratch, so no drive reads or writes the real home
# or /tmp. When app.sh defines app_env, it is called with the scratch
# directory and can append entries to VERIFY_ENV. verify_isolated and
# command.txt both read this one array, so the recorded command replays
# the same run.
verify_isolated_env() {
    local scratch="$1"
    VERIFY_ENV=(
        HOME="$scratch/home"
        TMPDIR="$scratch/tmp"
        XDG_CACHE_HOME="$scratch/home/.cache"
        XDG_CONFIG_HOME="$scratch/home/.config"
    )
    if declare -F app_env > /dev/null; then
        app_env "$scratch"
    fi
}

# verify_isolated <scratch dir> <cmd...>: run a command under VERIFY_ENV.
verify_isolated() {
    local scratch="$1"
    shift
    mkdir -p "$scratch/home" "$scratch/tmp"
    verify_isolated_env "$scratch"
    env "${VERIFY_ENV[@]}" "$@"
}

# --- The evidence keeper ---------------------------------------------------

# verify_drive <scratch dir> <evidence dir> <cmd...>: run a command from the
# scratch directory under VERIFY_ENV and keep command.txt, stdout.txt,
# stderr.txt and exit_code.txt in the evidence directory. Set VERIFY_RC to
# the exit code of the command. Never fail on it: the drive script judges
# the exit code. VERIFY_ENV is built once, so app_env runs once, and the run
# and command.txt use the same entries.
verify_drive() {
    local scratch="$1" evidence="$2"
    shift 2
    verify_isolated_env "$scratch"
    {
        printf 'cd %q &&\n' "$scratch"
        printf 'env'
        printf ' %q' "${VERIFY_ENV[@]}"
        printf ' \\\n'
        printf '%q ' "$@"
        printf '\n'
    } > "$evidence/command.txt"
    mkdir -p "$scratch/home" "$scratch/tmp"
    VERIFY_RC=0
    (cd "$scratch" && env "${VERIFY_ENV[@]}" "$@") \
        > "$evidence/stdout.txt" 2> "$evidence/stderr.txt" || VERIFY_RC=$?
    echo "$VERIFY_RC" > "$evidence/exit_code.txt"
}

# verify_readback <evidence dir> <cmd...>: run the read-back command, keep
# readback.txt and readback_exit_code.txt, print the read-back, and fail
# unless it exits 0.
verify_readback() {
    local evidence="$1"
    shift
    local rb=0
    "$@" > "$evidence/readback.txt" 2>&1 || rb=$?
    echo "$rb" > "$evidence/readback_exit_code.txt"
    cat "$evidence/readback.txt"
    [[ "$rb" -eq 0 ]] || verify_die "read-back failed; evidence in $evidence"
}

# --- The run's compose project ---------------------------------------------
#
# app.sh supplies the compose files and the override path:
#   VERIFY_COMPOSE_FILES=(<file relative to the checkout>...)
#   app_compose_override() { echo "<run dir>/scratch/.../override.yaml"; }

# verify_compose_project <run dir>: print verify-<app>-<run id>.
verify_compose_project() {
    echo "verify-$VERIFY_APP-$(basename "$1")"
}

# verify_compose <run dir> <compose args...>: the one place that builds the
# docker compose arguments. Every call (up, port, ps, down) passes the same
# project directory, the same -f files and the same -p name, so no call can
# reach another compose project or load a docker-compose.override.yaml with
# fixed host ports.
verify_compose() {
    local run_dir="$1"
    shift
    declare -F app_compose_override > /dev/null \
        || verify_die "app.sh defines no app_compose_override"
    [[ -n "${VERIFY_COMPOSE_FILES[*]+set}" ]] \
        || verify_die "app.sh sets no VERIFY_COMPOSE_FILES"
    local override file
    override="$(app_compose_override "$run_dir")"
    [[ -f "$override" ]] \
        || verify_die "$override is missing (run the launch script of the run's services)"
    local args=(--project-directory "$VERIFY_CHECKOUT")
    for file in "${VERIFY_COMPOSE_FILES[@]}"; do
        args+=(-f "$VERIFY_CHECKOUT/$file")
    done
    args+=(-f "$override" -p "$(verify_compose_project "$run_dir")")
    docker compose "${args[@]}" "$@"
}

# verify_project_containers <run dir>: print the IDs of every container,
# running or not, that carries the label of the run's compose project.
verify_project_containers() {
    docker ps -aq --filter "label=com.docker.compose.project=$(verify_compose_project "$1")"
}

# verify_check_project_free <run dir>: fail unless no container carries the
# label of the run's compose project. The project name is global to the
# host, but a run id is unique only in one checkout: another worktree, or a
# leftover of a run whose .verify/ was deleted, can use the same name. A
# second `up` on that name would recreate the container of the other run.
verify_check_project_free() {
    local project ids
    project="$(verify_compose_project "$1")"
    ids="$(verify_project_containers "$1")" \
        || verify_die "FAIL: docker ps failed for compose project $project"
    [[ -z "$ids" ]] || verify_die "FAIL: compose project $project already has containers: ${ids//$'\n'/ }.
    Another checkout or an old run uses this run id. Launch a new run with another run id."
}
