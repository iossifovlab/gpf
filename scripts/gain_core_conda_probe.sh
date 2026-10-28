#!/usr/bin/env bash
# Probe anaconda.org for a gain-core conda package. Run by the
# `Pre-flight: tag freshness` stage of Jenkinsfile.release when the
# operator sets GAIN_PIN_VERSION: it needs only curl.
#
# Input (environment): GAIN_PIN_VERSION.
#
# The script probes the public anaconda.org API, bioconda first and then
# iossifovlab. Exit 0 means that one of the two channels has gain-core
# GAIN_PIN_VERSION. Exit 1 means that neither channel has it: any HTTP
# code other than 200, a network failure included, counts as absent. An
# empty GAIN_PIN_VERSION exits 2.
set -u

if [ -z "${GAIN_PIN_VERSION:-}" ]; then
    echo "gain_core_conda_probe.sh: GAIN_PIN_VERSION is not set" >&2
    exit 2
fi

code() {
    # curl prints 000 and exits non-zero on a network failure.
    curl -sS -o /dev/null -w '%{http_code}' "$1" || true
}

# bioconda first: iossifovlab/gain#1967 stops the iossifovlab upload.
for channel in bioconda iossifovlab; do
    url="https://api.anaconda.org/release/${channel}/gain-core/${GAIN_PIN_VERSION}"
    http=$(code "$url")
    echo "Gain conda probe: HTTP $http for $url"
    if [ "$http" = "200" ]; then
        echo "Gain conda probe: gain-core ${GAIN_PIN_VERSION} present on ${channel}"
        exit 0
    fi
done

echo "ERROR: gain-core ${GAIN_PIN_VERSION} not found on the conda" \
     "channels bioconda and iossifovlab." \
     "The conda packages would pin a gain-core nobody can install." \
     "Bioconda lags a gain release by days, so a new version can be" \
     "missing there. Check https://anaconda.org/bioconda/gain-core" \
     "and https://anaconda.org/iossifovlab/gain-core, and re-trigger" \
     "with a valid GAIN_PIN_VERSION." >&2
exit 1
