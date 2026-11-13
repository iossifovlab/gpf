#!/usr/bin/env bash
# Probe anaconda.org for a gain-core conda package. Run by the
# `Pre-flight: tag freshness` stage of Jenkinsfile.release when the
# operator sets GAIN_PIN_VERSION: it needs only curl.
#
# Input (environment): GAIN_PIN_VERSION.
#
# The script probes the public anaconda.org API for the iossifovlab
# channel, which keeps gain-core for every gain release. Exit 0 means
# that iossifovlab has gain-core GAIN_PIN_VERSION. Exit 1 means that it
# does not: any HTTP code other than 200, a network failure included,
# counts as absent. An empty GAIN_PIN_VERSION exits 2.
set -u

if [ -z "${GAIN_PIN_VERSION:-}" ]; then
    echo "gain_core_conda_probe.sh: GAIN_PIN_VERSION is not set" >&2
    exit 2
fi

url="https://api.anaconda.org/release/iossifovlab/gain-core/${GAIN_PIN_VERSION}"
# curl prints 000 and exits non-zero on a network failure.
http=$(curl -sS -o /dev/null -w '%{http_code}' "$url" || true)
echo "Gain conda probe: HTTP $http for $url"
if [ "$http" = "200" ]; then
    echo "Gain conda probe: gain-core ${GAIN_PIN_VERSION} present on iossifovlab"
    exit 0
fi

echo "ERROR: gain-core ${GAIN_PIN_VERSION} not found on the conda" \
     "channel iossifovlab." \
     "The conda packages would pin a gain-core nobody can install." \
     "Check https://anaconda.org/iossifovlab/gain-core, and re-trigger" \
     "with a valid GAIN_PIN_VERSION." >&2
exit 1
