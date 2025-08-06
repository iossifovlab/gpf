#!/usr/bin/bash

for d in /wd/dae /wd/spliceai_annotator; do
    cd ${d};
    /opt/conda/bin/conda run --no-capture-output -n gpf pip install .
done

/opt/conda/bin/conda env list

export XLA_FLAGS=--xla_gpu_cuda_data_dir=/opt/conda/envs/gpf

nvidia-smi

mkdir -p /wd/test-results
cd /wd/spliceai_annotator/

/opt/conda/bin/conda run --no-capture-output -n gpf \
    py.test -vv -s --log-level=DEBUG \
        --cov-config /wd/coveragerc \
        --cov spliceai_annotator \
        --junitxml=/wd/results/spliceai-annotator-tests-junit.xml \
        /wd/spliceai_annotator/tests

/opt/conda/bin/conda run -n gpf \
    coverage xml

cp /wd/spliceai_annotator/coverage.xml /wd/test-results/

/opt/conda/bin/conda run -n gpf \
    coverage html --title gpf_spliceai_annotator -d /wd/test-results/coverage-html
