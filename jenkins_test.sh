#!/usr/bin/env bash

export PATH=${DAE_SOURCE_DIR}/tools:$PATH
export PATH=${DAE_SOURCE_DIR}/tests:$PATH
export PYTHONPATH=${DAE_SOURCE_DIR}:$PYTHONPATH
export PYTHONPATH=${DAE_SOURCE_DIR}/tools:$PYTHONPATH

rm -rf coverage/ && mkdir coverage && \
py.test --traceconfig -v --cov-config coveragerc \
    --junitxml=coverage/dae-junit.xml \
    --cov-report html:coverage/coverage.html \
    --cov-report xml:coverage/coverage.xml \
    --cov annotation \
    --cov backends \
    --cov common \
    --cov common_reports \
    --cov configurable_entities \
    --cov gene \
    --cov pedigrees \
    --cov pheno \
    --cov studies \
    --cov tools \
    --cov utils \
    --cov variant_annotation \
    --cov variants \
    DAE/tests/ \
    DAE/annotation/tests \
    DAE/backends/tests \
    DAE/common/tests/ \
    DAE/common_reports/tests \
    DAE/configurable_entities/tests \
    DAE/gene/tests \
    DAE/pedigrees/tests \
    DAE/pheno/tests \
    DAE/pheno_browser/tests \
    DAE/studies/tests \
    DAE/tools/tests \
    DAE/utils/tests \
    DAE/variant_annotation/tests \
    DAE/variants/tests/ && \
py.test -v --cov-config coveragerc \
    --junitxml=coverage/wdae-junit.xml \
    --cov-append \
    --cov-report html:coverage/coverage.html \
    --cov-report xml:coverage/coverage.xml \
    --cov annotation \
    --cov backends \
    --cov common \
    --cov common_reports \
    --cov configurable_entities \
    --cov gene \
    --cov pedigrees \
    --cov pheno \
    --cov studies \
    --cov tools \
    --cov utils \
    --cov variant_annotation \
    --cov variants \
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
    --cov users_api \
    wdae/datasets_api/tests \
    wdae/genotype_browser/tests \
    wdae/pheno_browser_api/tests
