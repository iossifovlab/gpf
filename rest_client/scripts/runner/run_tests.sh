#!/bin/bash
set -euo pipefail

# Runner entrypoint for the rest_client integration test stack. Runs
# pytest against the live backend (--url) and MailHog (--mailhog).
# JUnit + coverage XMLs land in /reports, mounted by the Jenkins job.

mkdir -p /reports

cd /workspace/rest_client

set +e
pytest -vv --log-level=DEBUG \
    --junitxml=/reports/pytest.xml \
    --cov=rest_client --cov-branch \
    --cov-report=xml:/reports/coverage.xml \
    tests/ \
    --url http://backend:21011 \
    --mailhog http://mail:8025
pytest_exit=$?

# Rewrite container-absolute paths so Jenkins recordCoverage can find sources.
sed -i "s#<source>/workspace/\([^<]*\)</source>#<source>\1</source>#g" \
    /reports/coverage.xml 2>/dev/null || true

chmod -R a+rw /reports
exit $pytest_exit
