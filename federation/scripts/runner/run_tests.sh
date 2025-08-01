#!/usr/bin/bash

for d in /wd/dae /wd/wdae /wd/rest_client /wd/federation; do
    cd ${d};
    /opt/conda/bin/conda run --no-capture-output -n gpf pip install .
done


cd /wd/federation/
/opt/conda/bin/conda run --no-capture-output -n gpf \
    py.test -vv -s --log-level=DEBUG \
        --cov-config /wd/coveragerc \
        --cov federation \
        --junitxml=/wd/results/federation-tests-junit.xml \
        /wd/federation/tests

/opt/conda/bin/conda run -n gpf \
    coverage xml

cp /wd/federation/coverage.xml /wd/test-results/

/opt/conda/bin/conda run -n gpf \
    coverage html --title gpf_federation -d /wd/test-results/coverage-html
