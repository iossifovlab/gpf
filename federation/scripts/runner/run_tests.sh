#!/usr/bin/bash

for d in /wd/dae /wd/wdae /wd/rest_client /wd/federation; do
    cd ${d};
    /opt/conda/bin/conda run --no-capture-output -n gpf pip install .
done


cd /wd/federation/
/opt/conda/bin/conda run --no-capture-output -n gpf \
    py.test -vv -s --log-level=DEBUG \
        --junitxml=/wd/results/federation-tests-junit.xml \
        tests/
