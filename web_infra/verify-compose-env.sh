#!/bin/sh
# Fail the build unless the e2e compose stack resolves the GRR cache
# bind and the container uid to the values we actually intend.
#
# WHY THIS EXISTS
# ---------------
# gain-web-e2e #1042 (same compose pattern, same bug here) came up green-ish
# while being silently wrong:
# `docker inspect` on the live container showed
#
#     <workspace>/web_infra/grr_cache -> /grr_cache      (not ${HOME}/grr_cache)
#     User = 0:0                                         (not the agent uid)
#
# i.e. compose had taken the `${GRR_CACHE_DIR:-./grr_cache}` and
# `${AGENT_UID:-0}:${AGENT_GID:-0}` *fallbacks* even though the pipeline's
# `environment{}` block sets all three. The persistent-cache design and the
# non-root design were both inert, and nothing said so: the cache landed in
# the workspace (wiped by the next build's cleanup) and every resource was
# re-downloaded, as root, forever.
#
# A silent fallback to a workspace-local cache running as root is exactly the
# bug this file guards. It must never pass quietly again — so this script
# asserts on the RESOLVED config (`docker compose config`), not on what we
# think we exported, and it fails loudly with expected-vs-actual.
#
# It also enforces the third leg, which #1042 got wrong in a different way:
# gpf's instance-import container never received GRR_DEFINITION_FILE, so it
# fell back to the image's baked-in default GRR (grr.iossifovlab.com) and
# cached nothing. Every service that constructs a GRR needs ALL THREE of:
# the /grr_cache bind, GRR_DEFINITION_FILE, and a non-root user.
#
# USAGE
#   web_infra/verify-compose-env.sh <env-file> <compose.yaml> [<overlay.yaml>]
#
# INPUTS (environment)
#   GRR_CACHE_DIR        required — the bind source every /grr_cache mount
#                        must resolve to, exactly.
#   EXPECT_GRR_SERVICES  required — space-separated services that MUST have
#                        all three legs.
#   ROOT_OK_SERVICES     optional — space-separated subset of the above that
#                        is allowed to stay root (documented exceptions only).
#   WORKSPACE            optional — if set, GRR_CACHE_DIR must NOT live under
#                        it (that is the fallback-into-the-workspace bug).
#   HOME                 optional — if set, GRR_CACHE_DIR must live under it.
set -eu

ENV_FILE="${1:?usage: verify-compose-env.sh <env-file> <compose.yaml> [overlay]}"
COMPOSE_FILE="${2:?usage: verify-compose-env.sh <env-file> <compose.yaml> [overlay]}"
OVERLAY="${3:-}"

: "${GRR_CACHE_DIR:?GRR_CACHE_DIR must be set}"
: "${EXPECT_GRR_SERVICES:?EXPECT_GRR_SERVICES must be set}"
ROOT_OK_SERVICES="${ROOT_OK_SERVICES:-}"

fail() {
    echo "" >&2
    echo "================ COMPOSE ENV VERIFICATION FAILED ================" >&2
    echo "$@" >&2
    echo "================================================================" >&2
    exit 1
}

[ -f "$ENV_FILE" ] || fail "env-file not found: $ENV_FILE"

case "$GRR_CACHE_DIR" in
    /*) ;;
    *) fail "GRR_CACHE_DIR must be an absolute path.
    expected: an absolute path under \$HOME
    actual:   '$GRR_CACHE_DIR'" ;;
esac

# The whole point of the cache is that it OUTLIVES the build. A cache inside
# the workspace is deleted by the next build's cleanup — that is the #1042
# bug verbatim, so reject it before docker is even consulted.
if [ -n "${WORKSPACE:-}" ]; then
    case "$GRR_CACHE_DIR/" in
        "$WORKSPACE"/*) fail "GRR_CACHE_DIR resolves INSIDE the Jenkins workspace.
    This is the gain-web-e2e #1042 bug: the cache would be wiped by the
    next build's cleanup and every GRR resource re-downloaded.
    expected: a path under \$HOME, outside \$WORKSPACE
    actual:   '$GRR_CACHE_DIR'
    workspace: '$WORKSPACE'" ;;
    esac
fi

if [ -n "${HOME:-}" ]; then
    case "$GRR_CACHE_DIR/" in
        "$HOME"/*) ;;
        *) fail "GRR_CACHE_DIR is not under \$HOME.
    expected: a path under '$HOME'
    actual:   '$GRR_CACHE_DIR'" ;;
    esac
fi

set -- --env-file "$ENV_FILE" -f "$COMPOSE_FILE"
[ -n "$OVERLAY" ] && set -- "$@" -f "$OVERLAY"

CONFIG="$(docker compose "$@" config)" \
    || fail "\`docker compose config\` failed — the stack does not even resolve."

# The dead NFS GRR must be gone everywhere, in every service, in both modes.
if printf '%s\n' "$CONFIG" | grep -q '/mnt/cephfs'; then
    fail "a /mnt/cephfs bind survives in the resolved config:
$(printf '%s\n' "$CONFIG" | grep -n '/mnt/cephfs')
    The NFS GRR died with piglet; nothing may reference it."
fi

# Parse the RESOLVED config. Indent anchors are exact: compose's canonical
# output puts service names at 2 spaces, service keys at 4, environment keys
# at 6, and volume entry keys at 8 — so these patterns cannot accidentally
# match a value that merely looks like a key.
TABLE="$(printf '%s\n' "$CONFIG" | awk '
    /^services:$/ { in_svc = 1; next }
    /^[a-zA-Z]/   { in_svc = 0 }
    !in_svc       { next }
    /^  [^ ]/ {
        svc = $1; sub(/:$/, "", svc)
        order[++n] = svc
        next
    }
    /^        source: /              { src = $2 }
    /^        target: \/grr_cache$/  { cache[svc] = src }
    /^    user: /                    { u = $2; gsub(/['"'"'"]/, "", u); user[svc] = u }
    /^      GRR_DEFINITION_FILE: /   { grrdef[svc] = $2 }
    END {
        for (i = 1; i <= n; i++) {
            s = order[i]
            printf "%s\t%s\t%s\t%s\n", s, \
                (s in cache  ? cache[s]  : "-"), \
                (s in user   ? user[s]   : "0:0"), \
                (s in grrdef ? grrdef[s] : "-")
        }
    }
')"

echo "resolved compose config: $COMPOSE_FILE ${OVERLAY:+
                        + $OVERLAY}"
echo "expected /grr_cache bind source: $GRR_CACHE_DIR"
echo ""
printf '%-24s %-40s %-12s %s\n' SERVICE /grr_cache-BIND-SOURCE USER GRR_DEFINITION_FILE
printf '%-24s %-40s %-12s %s\n' ------- --------------------- ---- -------------------
printf '%s\n' "$TABLE" | while IFS="$(printf '\t')" read -r svc src usr def; do
    printf '%-24s %-40s %-12s %s\n' "$svc" "$src" "$usr" "$def"
done
echo ""

errors=""
note() { errors="${errors}
  - $1"; }

# (1) Anti-vacuity. A check that matches nothing asserts nothing — this repo
#     has been bitten by that more than once. If NO service binds /grr_cache,
#     the parser or the compose file broke and every check below is a no-op.
bound=$(printf '%s\n' "$TABLE" | awk -F'\t' '$2 != "-"' | wc -l)
[ "$bound" -ge 1 ] || fail "no service binds /grr_cache at all.
    Either the compose file lost the mount or this parser stopped matching.
    Refusing to pass a check that asserts nothing."

# (2) EVERY /grr_cache bind in the file — not just the expected ones — must
#     resolve to GRR_CACHE_DIR. This is the check that catches the fallback.
while IFS="$(printf '\t')" read -r svc src _usr _def; do
    [ "$src" = "-" ] && continue
    [ "$src" = "$GRR_CACHE_DIR" ] && continue
    note "$svc: /grr_cache bind source is wrong (compose took the fallback?)
      expected: $GRR_CACHE_DIR
      actual:   $src"
done <<EOF
$TABLE
EOF

# (3) Every service that builds a GRR needs all three legs.
for svc in $EXPECT_GRR_SERVICES; do
    row=$(printf '%s\n' "$TABLE" | awk -F'\t' -v s="$svc" '$1 == s')
    if [ -z "$row" ]; then
        note "$svc: expected to exist in the resolved config, but it does not."
        continue
    fi
    src=$(printf '%s' "$row" | cut -f2)
    usr=$(printf '%s' "$row" | cut -f3)
    def=$(printf '%s' "$row" | cut -f4)

    [ "$src" = "-" ] && note "$svc: has NO /grr_cache bind.
      expected: $GRR_CACHE_DIR mounted at /grr_cache
      actual:   no bind — this service would cache nothing."

    if [ "$def" = "-" ]; then
        note "$svc: has NO GRR_DEFINITION_FILE.
      It would silently fall back to the image's baked-in default GRR
      (the gain-web-e2e #1042 instance-import bug) and cache nothing."
    fi

    root_ok=no
    for ok in $ROOT_OK_SERVICES; do
        [ "$ok" = "$svc" ] && root_ok=yes
    done
    if [ "$usr" = "0:0" ] && [ "$root_ok" = no ]; then
        note "$svc: resolved user is 0:0 (root) — compose took the
      \${AGENT_UID:-0}:\${AGENT_GID:-0} fallback.
      expected: a non-root uid:gid (the agent's)
      actual:   0:0
      Root-owned entries in the shared cache cannot be pruned by 'jenkins'."
    fi
done

[ -z "$errors" ] || fail "the resolved compose config is not what this
pipeline intends:$errors"

echo "OK: /grr_cache binds to $GRR_CACHE_DIR in every service that mounts it;"
# tr -s: collapse any line-continuation whitespace the caller's shell left
# in the list, so the log line reads cleanly.
expect_pretty=$(printf '%s' "$EXPECT_GRR_SERVICES" | tr -s ' ')
echo "OK: all of [$expect_pretty] carry a GRR definition + cache bind;"
echo "OK: non-root uid enforced${ROOT_OK_SERVICES:+ (documented root exception: $ROOT_OK_SERVICES)};"
echo "OK: no /mnt/cephfs bind anywhere in the resolved config."
