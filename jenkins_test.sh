#!/usr/bin/env bash

export PATH=${DAE_SOURCE_DIR}/tools:$PATH
export PATH=${DAE_SOURCE_DIR}/tests:$PATH
export PYTHONPATH=${DAE_SOURCE_DIR}:$PYTHONPATH
export PYTHONPATH=${DAE_SOURCE_DIR}/tools:$PYTHONPATH

rm -rf coverage/ && mkdir coverage && \

py.test --traceconfig -v --cov-config coveragerc --reimport \
    --junitxml=coverage/dae-junit.xml \
    --cov-report html:coverage/coverage.html \
    --cov-report xml:coverage/coverage.xml \
    --cov annotation \
    --cov backends \
    --cov common \
    --cov common_reports \
    --cov configurable_entities \
    --cov enrichment_tool \
    --cov gene \
    --cov pedigrees \
    --cov pheno \
    --cov pheno_browser \
    --cov studies \
    --cov tests \
    --cov tools \
    --cov utils \
    --cov variant_annotation \
    --cov variants \
    dae/

py.test -v --cov-config coveragerc \
    --junitxml=coverage/wdae-junit.xml \
    --cov-append \
    --cov-report html:coverage/coverage.html \
    --cov-report xml:coverage/coverage.xml \
    --cov chromosome \
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
    --cov query_state_save \
    --cov tests \
    --cov tools \
    --cov users_api \
    --cov wdae \
    wdae/


chmod a+rwx -R coverage

rm -rf \
	wdae-api.log wdae-debug.log \
	wdae_django_default.cache wdae_django_pre.cache

find . -name "*.pyc" -delete
