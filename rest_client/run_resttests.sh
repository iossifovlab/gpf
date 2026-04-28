#!/bin/bash

for d in /wd/core /wd/web /wd/rest_client; do
    cd ${d};
    /opt/conda/bin/conda run --no-capture-output -n gpf pip install -e .
done

#/opt/conda/bin/conda run --no-capture-output -n gpf \
/opt/conda/bin/conda run -n gpf \
    py.test -vv -s --log-level=DEBUG \
        --junitxml=/wd/test-results/resttests-junit.xml \
        --cov-config /wd/coveragerc \
        --cov rest_client \
        /wd/rest_client/tests \
        --url http://backend:21011 \
        --mailhog http://mail:8025

/opt/conda/bin/conda run -n gpf \
    coverage xml

cp /wd/rest_client/coverage.xml /wd/test-results/

/opt/conda/bin/conda run -n gpf \
    coverage html --title rest_client -d /wd/test-results/coverage-html

