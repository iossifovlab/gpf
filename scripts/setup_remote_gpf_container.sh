#!/bin/bash

if [[ -z $WD ]]; then
    SCRIPT_LOCATION=$(readlink -f "$0")
    SCRIPT_DIR=$(dirname "${SCRIPT_LOCATION}")
    export WD=$(dirname "${SCRIPT_DIR}")
fi

docker pull seqpipe/seqpipe-gpf-conda

if [[ ! -d $WD/gpf_remote ]]; then
    $WD/wdae/wdae/wdae_bootstrap.sh hg19 $WD/gpf_remote
fi

wget -P $WD -c https://iossifovlab.com/distribution/public/studies/genotype-iossifov_2014-latest.tar.gz
tar -zxvf genotype-iossifov_2014-latest.tar.gz

#(. ./gpf_remote/setenv.sh; cd ./iossifov_2014; \
    #$WD/dae/dae/tools/simple_study_import.py IossifovWE2014.ped --denovo-file IossifovWE2014.tsv --id iossifov_2014)

#LOCAL_DATA_DIR="$WD/scripts/gpf_remote"

#sed -i -e "s@$LOCAL_DATA_DIR@/data@g" ./gpf_remote/studies/iossifov_2014/iossifov_2014.conf
