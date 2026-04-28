#!/usr/bin/bash

rm -rf /wd/data/data-hg19-resttest
mkdir -p /wd/data/data-hg19-resttest

cp -r /wd/rest_client/integration/data/* /wd/data/data-hg19-resttest/

mkdir -p /wd/data/data-hg19-resttest/pheno/images
