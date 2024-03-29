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

export LD_LIBRARY_PATH=/opt/conda/envs/gpf/lib/native:/opt/conda/envs/gpf/lib/server

export MPLBACKEND=PDF
# export MPLBACKEND=qt5agg

sed -i "s/localhost/impala/" /code/dae_conftests/dae_conftests/tests/fixtures/DAE.conf

cd /code/

if [[ $CLEANUP ]]; then
    echo "Cleaning up with reimport..."
    py.test -v -s \
        --reimport \
        --cov-config /code/coveragerc \
        --junitxml=./test_results/dae-junit.xml \
        --cov-report=html:/code/test_results/coverage.html \
        --cov-report=xml:/code/test_results/coverage.xml \
        --cov dae/ \
        dae/dae/

else

    py.test -v -s \
        --cov-config /code/coveragerc \
        --junitxml=./test_results/dae-junit.xml \
        --cov-report=html:/code/test_results/coverage.html \
        --cov-report=xml:/code/test_results/coverage.xml \
        --cov dae/ \
        dae/dae/

fi

cd /code/

py.test -v -s --cov-config /code/coveragerc \
    --junitxml=/code/test_results/wdae-junit.xml \
    --cov-append \
    --cov-report=html:/code/test_results/coverage.html \
    --cov-report=xml:/code/test_results/coverage.xml \
    --cov wdae/ \
    wdae/wdae


cd /code
chmod a+rwx -R /code/test_results

git checkout dae_conftests/dae_conftests/tests/fixtures/DAE.conf
