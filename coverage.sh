#!/usr/bin/env bash
py.test -v --cov-config coveragerc \
    --junitxml=DAE/junit.xml \
    --cov-append \
    --cov-report html \
    --cov-report xml \
    --cov tools \
    DAE/tools/tests
