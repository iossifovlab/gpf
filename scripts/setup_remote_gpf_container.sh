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
tar -zxvf $WD/genotype-iossifov_2014-latest.tar.gz -C $WD

wget -P $WD -c https://iossifovlab.com/distribution/public/pheno/phenotype-comp-data-latest.tar.gz
tar -zxvf $WD/phenotype-comp-data-latest.tar.gz -C $WD

sed -i 's/dae_data_dir =.*/dae_data_dir = "."/' $WD/gpf_remote/DAE.conf
sed -i 's/wd =.*/wd = "."/' $WD/gpf_remote/DAE.conf

#(. ./gpf_remote/setenv.sh; cd ./iossifov_2014; \
    #$WD/dae/dae/tools/simple_study_import.py IossifovWE2014.ped --denovo-file IossifovWE2014.tsv --id iossifov_2014)

#LOCAL_DATA_DIR="$WD/scripts/gpf_remote"

#sed -i -e "s@$LOCAL_DATA_DIR@/data@g" ./gpf_remote/studies/iossifov_2014/iossifov_2014.conf
