#!/bin/bash
set -euo pipefail

# Runner entrypoint for the federation integration test stack. Runs
# pytest against the live backend (TEST_REMOTE_HOST is set by compose).
# JUnit + coverage XMLs land in /reports, mounted by the Jenkins job.

mkdir -p /reports

cd /workspace/federation

set +e
pytest -vv --log-level=DEBUG \
    --junitxml=/reports/pytest.xml \
    --cov=federation --cov-branch \
    --cov-report=xml:/reports/coverage.xml \
    tests/
pytest_exit=$?

# Rewrite container-absolute paths so Jenkins recordCoverage can find sources.
sed -i "s#<source>/workspace/\([^<]*\)</source>#<source>\1</source>#g" \
    /reports/coverage.xml 2>/dev/null || true

chmod -R a+rw /reports
exit $pytest_exit
