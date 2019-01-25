#!/usr/bin/env bash

export PATH=${DAE_SOURCE_DIR}/tools:$PATH
export PATH=${DAE_SOURCE_DIR}/tests:$PATH
export PYTHONPATH=${DAE_SOURCE_DIR}:$PYTHONPATH
export PYTHONPATH=${DAE_SOURCE_DIR}/tools:$PYTHONPATH

py.test --runslow --withspark -v --cov-config coveragerc \
    --junitxml=coverage/dae-junit.xml \
    --cov-report html:coverage/coverage.html \
    --cov-report xml:coverage/coverage.xml \
    --cov-append \
    --cov common_reports_api \
    --cov datasets_api \
    --cov enrichment_api \
    --cov family_counters_api \
    --cov gene_sets \
    --cov gene_weights \
    --cov genotype_browser \
    --cov groups_api \
    --cov helpers \
    --cov measures_api \
    --cov pheno_browser_api \
    --cov pheno_tool_api \
    --cov precompute \
    --cov preloaded \
    --cov tools \
    --cov users_api \
    --cov common \
    --cov variant_annotation \
    --cov annotation \
    --cov variants \
    --cov backends \
    --cov studies \
    --cov study_groups \
    --cov datasets \
    --cov common_reports \
    --cov pedigrees \
    DAE/common/tests/ \
    DAE/variants/tests/ \
    DAE/variant_annotation/tests \
    DAE/annotation/tests \
    DAE/backends/tests \
    DAE/studies/tests \
    DAE/common_reports/tests \
    DAE/pedigrees/tests \
    DAE/gene/tests

    # DAE/study_groups/tests \
    # DAE/datasets/tests \
