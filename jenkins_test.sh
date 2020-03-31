#!/usr/bin/env bash

set -e

# export PATH=${DAE_SOURCE_DIR}/dae/tools:$PATH
# export PATH=${DAE_SOURCE_DIR}/dae/tests:$PATH
# export PYTHONPATH=${DAE_SOURCE_DIR}/dae:$PYTHONPATH
# export PYTHONPATH=${DAE_SOURCE_DIR}/dae/tools:$PYTHONPATH
cd /code

find . -name "*.pyc" -delete
rm -rf \
	wdae-api.log wdae-debug.log \
	wdae_django_default.cache wdae_django_pre.cache

# rm -rf test_results/ && mkdir test_results

cd dae && pip install -e . && cd -
cd wdae && pip install -e . && cd -
cd dae_conftests && pip install -e . && cd -

export DAE_HDFS_HOST=impala
export DAE_IMPALA_HOST=impala
export HADOOP_HOME=/opt/conda/envs/gpf

py.test -v --cov-config coveragerc \
    --reimport \
    --junitxml=./test_results/dae-junit.xml \
    --cov-report=html:./test_results/coverage.html \
    --cov-report=xml:./test_results/coverage.xml \
    --cov dae/ \
    dae/dae/

py.test -v --cov-config coveragerc \
    --junitxml=./test_results/wdae-junit.xml \
    --cov-append \
    --cov-report=html:./test_results/coverage.html \
    --cov-report=xml:./test_results/coverage.xml \
    --cov wdae/ \
    wdae/wdae


chmod a+rwx -R /code/test_results

