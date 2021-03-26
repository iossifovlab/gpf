#!/usr/bin/env bash

set -e

if [ -z ${WORKSPACE} ];
then
    export WORKSPACE=`pwd`
fi

if [ -z ${WD} ];
then
    export WD=${WORKSPACE}
fi

echo "WORKSPACE                     : ${WORKSPACE}"
echo "WD                            : ${WD}"


. ${WD}/scripts/env.sh 

echo "DAE_DB_DIR                    : ${DAE_DB_DIR}"

for d in /code/dae /code/wdae /code/dae_conftests; do
    cd ${d}
    pip install -e .
done


cd /code/wdae

PYTHONHASHSEED=0 py.test -v -n 10 \
    --cov-config /code/coveragerc \
    --junitxml=/code/results/wdae-junit.xml \
    --cov-report=html:/code/results/wdae-coverage.html \
    --cov-report=xml:/code/results/wdae-coverage.xml \
    --cov /code/wdae/ \
    wdae

