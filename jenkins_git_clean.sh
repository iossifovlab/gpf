#!/bin/sh

cd /code && \
    git clean -xdf \
        -e data-hg19-startup*.tar.gz \
        -e data-hg19-startup \
        -e builds \
        -e test_results || true