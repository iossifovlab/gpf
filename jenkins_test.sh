#!/usr/bin/env bash

export PATH=${DAE_SOURCE_DIR}/dae/tools:$PATH
export PATH=${DAE_SOURCE_DIR}/dae/tests:$PATH
export PYTHONPATH=${DAE_SOURCE_DIR}/dae:$PYTHONPATH
export PYTHONPATH=${DAE_SOURCE_DIR}/dae/tools:$PYTHONPATH

rm -rf coverage/ && mkdir coverage

cd dae && pip install -e . && cd -
cd wdae && pip install -e . && cd -

py.test -v --cov-config coveragerc \
    --reimport \
    --junitxml=coverage/dae-junit.xml \
    --cov-report=html:./coverage/coverage.html \
    --cov-report=xml:./coverage/coverage.xml \
    --cov dae/ \
    dae/dae/

py.test -v --cov-config coveragerc \
    --junitxml=coverage/wdae-junit.xml \
    --cov-append \
    --cov-report=html:./coverage/coverage.html \
    --cov-report=xml:./coverage/coverage.xml \
    --cov wdae/ \
    wdae/wdae


chmod a+rwx -R coverage

rm -rf \
	wdae-api.log wdae-debug.log \
	wdae_django_default.cache wdae_django_pre.cache

find . -name "*.pyc" -delete
