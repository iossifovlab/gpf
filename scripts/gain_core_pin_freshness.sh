#!/usr/bin/env bash
# Warn when GAIN_PIN_VERSION is older than the newest gain-core on the
# iossifovlab conda channel (gpf#1207). Run by the
# `Pre-flight: tag freshness` stage of Jenkinsfile.release when the
# operator sets GAIN_PIN_VERSION: it needs only curl.
#
# Input (environment): GAIN_PIN_VERSION.
#
# The script reads `latest_version` from the public anaconda.org API
# and compares it with the pin as numbers, field by field. It only
# gives advice: it exits 0 in every case. An older pin can be a
# deliberate choice of the operator.
set -u

# No pin: the release bundles the gain wheel that gpf-master CI tested
# with, so there is nothing to compare.
if [ -z "${GAIN_PIN_VERSION:-}" ]; then
    echo "Gain pin freshness: GAIN_PIN_VERSION is not set; nothing to check"
    exit 0
fi

url="https://api.anaconda.org/package/iossifovlab/gain-core"
# A network failure or an HTTP error leaves the body empty.
body=$(curl -fsS --max-time 30 "$url" || true)

latest=$(printf '%s' "$body" \
    | grep -o '"latest_version"[[:space:]]*:[[:space:]]*"[^"]*"' \
    | head -n 1 \
    | sed 's/.*"\([^"]*\)"$/\1/')

# The check only gives advice: a missing or malformed latest_version
# prints a warning and passes. The existence probes stay fatal.
if ! [[ "$latest" =~ ^[0-9]+(\.[0-9]+)*$ ]]; then
    echo "WARNING: cannot read the newest gain-core version from" \
         "${url} (got '${latest}')." \
         "Skipping the freshness check of GAIN_PIN_VERSION" \
         "${GAIN_PIN_VERSION}."
    exit 0
fi

# Compare two dotted versions as numbers. Print -1, 0 or 1.
compare_versions() {
    local IFS=.
    local -a a b
    read -r -a a <<<"$1"
    read -r -a b <<<"$2"
    local n=${#a[@]}
    [ "${#b[@]}" -gt "$n" ] && n=${#b[@]}
    local i x y
    for ((i = 0; i < n; i++)); do
        x=$((10#${a[i]:-0}))
        y=$((10#${b[i]:-0}))
        if [ "$x" -lt "$y" ]; then echo -1; return; fi
        if [ "$x" -gt "$y" ]; then echo 1; return; fi
    done
    echo 0
}

if [ "$(compare_versions "$GAIN_PIN_VERSION" "$latest")" = "-1" ]; then
    echo "WARNING: GAIN_PIN_VERSION ${GAIN_PIN_VERSION} is older than" \
         "the newest gain-core ${latest} on iossifovlab." \
         "The release bundles gain-core ${GAIN_PIN_VERSION}." \
         "Re-trigger with GAIN_PIN_VERSION=${latest} unless the older" \
         "pin is deliberate."
else
    echo "Gain pin freshness: GAIN_PIN_VERSION ${GAIN_PIN_VERSION} is" \
         "not older than the newest gain-core ${latest} on iossifovlab"
fi
exit 0
