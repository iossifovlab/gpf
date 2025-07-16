#!/bin/bash
#/wait-for-it.sh backend:21010 -t 120

for d in /wd/dae /wd/wdae /wd/rest_client; do
    cd ${d};
    /opt/conda/bin/conda run --no-capture-output -n gpf pip install -e .
done

#/opt/conda/bin/conda run --no-capture-output -n gpf \
/opt/conda/bin/conda run -n gpf \
    py.test -vv -s --log-level=DEBUG \
        --junitxml=/wd/test-results/resttests-junit.xml \
        /wd/rest_client/rest_client/tests \
        --url http://backend:21010 \
        --mailhog http://mail:8025
