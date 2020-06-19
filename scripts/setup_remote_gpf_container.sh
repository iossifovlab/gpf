#!/bin/bash

docker pull seqpipe/seqpipe-gpf-conda

wdae_bootstrap.sh hg19 gpf_remote

wget -c https://iossifovlab.com/distribution/public/studies/genotype-iossifov_2014-latest.tar.gz
tar -zxvf genotype-iossifov_2014-latest.tar.gz

(. ./gpf_remote/setenv.sh; cd ./iossifov_2014; \
    simple_study_import.py IossifovWE2014.ped --denovo-file IossifovWE2014.tsv --id iossifov_2014)

LOCAL_DATA_DIR="$PWD/gpf_remote"

sed -i -e "s@$LOCAL_DATA_DIR@/data@g" ./gpf_remote/studies/iossifov_2014/iossifov_2014.conf
