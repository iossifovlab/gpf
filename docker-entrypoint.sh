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
SPA_INDEX=/var/www/html/index.html

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

exec "$@"
