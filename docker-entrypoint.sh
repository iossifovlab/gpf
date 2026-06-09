#!/bin/bash
# Entrypoint for the combined gpf-web image.
#
# When GPF_PREFIX is set, serve the app under /<prefix>/ instead of
# the document root: render the prefixed Apache vhost from
# httpd-combined.conf.template and repoint the SPA <base href>. When
# GPF_PREFIX is empty, do nothing — the image ships the root-serving
# httpd-combined.conf and <base href="/"> verbatim, so root
# deployments (and web_e2e / compose) are byte-for-byte unchanged.
#
# Then hand off (exec) to the image's CMD — supervisord, which
# foreground-runs gunicorn + apache2. apache2 reads the conf we
# render here, so this MUST run before supervisord starts it (it
# does: this is the ENTRYPOINT, supervisord is the CMD).
#
# Apache strips the prefix when proxying to gunicorn; Django carries
# it back via FORCE_SCRIPT_NAME (set from WDAE_PREFIX). gpf-infra
# sets GPF_PREFIX and WDAE_PREFIX to the same value.
set -euo pipefail

TEMPLATE=/etc/apache2/httpd-combined.conf.template
APACHE_CONF=/etc/apache2/apache2.conf
# Overridable so the index.html rewrites can be exercised against a
# fixture in tests; defaults to the image's real SPA index.
SPA_INDEX="${SPA_INDEX:-/var/www/html/index.html}"

# Normalise: "/gpf/" | "gpf" | "/gpf" -> "gpf"; unset/"" -> "".
prefix="${GPF_PREFIX:-}"
prefix="${prefix#/}"
prefix="${prefix%/}"

if [[ -n "$prefix" ]]; then
    echo "gpf-web entrypoint: serving under /${prefix}/ (GPF_PREFIX=${prefix})"

    # Render the prefixed vhost (token -> prefix path segment),
    # overwriting the shipped root config.
    sed "s|__GPF_PREFIX__|${prefix}|g" "$TEMPLATE" > "$APACHE_CONF"

    # Repoint the SPA. The new SPA is fully relative, so rewriting
    # this single line relocates assets + API + client-side routing
    # under the prefix. The generic match on the current value makes
    # it idempotent (safe across container restarts / re-renders).
    if [[ -f "$SPA_INDEX" ]]; then
        sed -i -E "s#<base href=\"[^\"]*\"#<base href=\"/${prefix}/\"#" "$SPA_INDEX"
    fi
else
    echo "gpf-web entrypoint: serving at document root (GPF_PREFIX unset)"
fi

# Google Analytics: inject a gtag.js snippet into the SPA index when
# GPF_GA_MEASUREMENT_ID is set; leave the SPA GA-free when it isn't, so
# the same image stays untracked on hosts that don't opt in (e.g. dory)
# and tracked where configured (SFARI). Marker-guarded + idempotent:
# every run first strips any prior gpf-ga block, then re-inserts from
# the current env value — so restarts and ID changes converge to exactly
# one block, and clearing the var removes it. The snippet is single-line
# so the rewrite stays sed-portable and correct whether the built
# index.html is minified or pretty-printed (same reasoning as the
# <base href> substring rewrite above). The sed output is written back
# into the existing file (`cat tmp > index`) rather than `mv`'d over it,
# so index.html keeps its original mode/owner — Apache runs as www-data
# and a mktemp-then-mv would leave the file root-only (0600) and serve
# 403. No atomicity concern: this runs before supervisord starts apache.
ga_id="${GPF_GA_MEASUREMENT_ID:-}"
if [[ -f "$SPA_INDEX" ]]; then
    strip='s#<!-- gpf-ga start -->.*<!-- gpf-ga end -->##g'
    ga_tmp="$(mktemp)"
    if [[ -n "$ga_id" ]]; then
        echo "gpf-web entrypoint: injecting Google Analytics tag (${ga_id})"
        snippet="<!-- gpf-ga start --><script async src=\"https://www.googletagmanager.com/gtag/js?id=${ga_id}\"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','${ga_id}');</script><!-- gpf-ga end -->"
        sed -e "$strip" -e "s#</head>#${snippet}</head>#" \
            "$SPA_INDEX" > "$ga_tmp" && cat "$ga_tmp" > "$SPA_INDEX"
    elif grep -q '<!-- gpf-ga start -->' "$SPA_INDEX"; then
        # No ID, but a block lingers from a previous tagged run: drop it.
        # When there's neither an ID nor a stale block we touch nothing,
        # so the GA-free root/e2e/compose index stays byte-for-byte intact.
        sed -e "$strip" "$SPA_INDEX" > "$ga_tmp" && cat "$ga_tmp" > "$SPA_INDEX"
    fi
    rm -f "$ga_tmp"
fi

exec "$@"
