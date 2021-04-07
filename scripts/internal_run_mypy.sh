#!/bin/bash

cd /code

cd /code/dae
mypy dae \
    --exclude dae/docs/ \
    --exclude dae/docs/conf.py \
    --pretty \
    --ignore-missing-imports \
    --warn-return-any \
    --warn-redundant-casts \
    --html-report /code/results/mypy/dae_report || true

cd /code/wdae
mypy wdae \
    --exclude wdae/docs/ \
    --exclude wdae/docs/conf.py \
    --exclude wdae/conftest.py \
    --pretty \
    --ignore-missing-imports \
    --warn-return-any \
    --warn-redundant-casts \
    --html-report /code/results/mypy/wdae_report || true

