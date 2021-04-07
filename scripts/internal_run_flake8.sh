#!/bin/bash

# conda init bash
# conda activate gpf


# cd /code && flake8 --format=pylint \
#     --exclude "--exclude \"*old*,*tmp*,*temp*,data-hg19*,gpf*\"" . > \
#     ./test_results/pyflakes.report || echo "pylint exited with $?"

cd /code && flake8 --format=html --htmldir=/code/results/flake8_report \
    --exclude "--exclude \"*old*,*tmp*,*temp*,data-hg19*,gpf*\"" . || true

exit 0
