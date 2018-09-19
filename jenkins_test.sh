#!/usr/bin/env bash

TEST_DATA="test_data"

export DAE_SOURCE_DIR=`pwd`/DAE
export DAE_DB_DIR=`pwd`/$TEST_DATA

export PATH=${DAE_SOURCE_DIR}/tools:$PATH
export PATH=${DAE_SOURCE_DIR}/tests:$PATH
export PYTHONPATH=${DAE_SOURCE_DIR}:$PYTHONPATH
export PYTHONPATH=${DAE_SOURCE_DIR}/tools:$PYTHONPATH

py.test -v --cov-config coveragerc \
    --junitxml=wdae/junit.xml \
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
    wdae/


py.test -v --nomysql --cov-config coveragerc \
    --junitxml=DAE/junit.xml \
    --cov-append \
    --cov-report html \
    --cov-report xml \
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
    DAE/
