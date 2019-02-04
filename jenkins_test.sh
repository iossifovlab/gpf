#!/usr/bin/env bash

export PATH=${DAE_SOURCE_DIR}/tools:$PATH
export PATH=${DAE_SOURCE_DIR}/tests:$PATH
export PYTHONPATH=${DAE_SOURCE_DIR}:$PYTHONPATH
export PYTHONPATH=${DAE_SOURCE_DIR}/tools:$PYTHONPATH

py.test --traceconfig -v --cov-config coveragerc \
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
    --cov studies \
    --cov study_groups \
    --cov datasets \
    --cov common_reports \
    --cov pedigrees \
    DAE/common/tests/ \
    DAE/variants/tests/ \
    DAE/variant_annotation/tests \
    DAE/annotation/tests \
    DAE/studies/tests \
    DAE/common_reports/tests \
    DAE/pedigrees/tests \
    DAE/gene/tests


py.test -v --cov-config coveragerc \
    --junitxml=coverage/wdae-junit.xml \
    --cov-report html:coverage/coverage.html \
    --cov-report xml:coverage/coverage.xml \
    --cov-append \
    --cov common_reports_api \
    --cov datasets_api \
    --cov enrichment_api \
    --cov family_counters_api \
    --cov gene_sets \
    --cov gene_weights \
    --cov genomic_scores_api \
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
    --cov annotation \
    --cov annotation_pipeline \
    --cov common \
    --cov datasets \
    --cov enrichment_tool \
    --cov gene \
    --cov pheno \
    --cov pheno_browser \
    --cov pheno_tool \
    --cov transmitted \
    --cov utils \
    wdae/datasets_api/tests
