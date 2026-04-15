#!/usr/bin/bash

for d in /wd/gain_core /wd/gpf_core /wd/gpf_web /wd/rest_client /wd/gpf_federation; do
    cd ${d};
    /opt/conda/bin/conda run --no-capture-output -n gpf pip install .
done


cd /wd/gpf_federation/
/opt/conda/bin/conda run --no-capture-output -n gpf \
    py.test -vv -s --log-level=DEBUG \
        --cov-config /wd/coveragerc \
        --cov federation \
        --junitxml=/wd/results/federation-tests-junit.xml \
        /wd/gpf_federation/tests

/opt/conda/bin/conda run -n gpf \
    coverage xml

cp /wd/gpf_federation/coverage.xml /wd/test-results/

/opt/conda/bin/conda run -n gpf \
    coverage html --title gpf_federation -d /wd/test-results/coverage-html
