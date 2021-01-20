#!/bin/bash

set -e

if [[ -z $WD ]]; then
    SCRIPT_LOCATION=$(readlink -f "$0")
    SCRIPT_DIR=$(dirname "${SCRIPT_LOCATION}")
    export WD=$(dirname "${SCRIPT_DIR}")
fi

export GPF_SERIES=$(python -c "from dae.__version__ import SERIES; print(SERIES)")

echo "GPF_SERIES=${GPF_SERIES}"


docker pull seqpipe/seqpipe-gpf-conda

if [[ ! -d $WD/gpf_remote ]]; then
    if [[ -d $WD/data-hg19-startup ]]; then
        cp -rva $WD/data-hg19-startup $WD/gpf_remote
    else
        $WD/wdae/wdae/wdae_bootstrap.sh hg19 $WD/gpf_remote
    fi
fi

if ls builds/genotype-iossifov_2014-*.tar.gz 1> /dev/null 2>&1; then
    cp builds/genotype-iossifov_2014-*.tar.gz $WD/genotype-iossifov_2014-latest.tar.gz
else
    wget -P $WD -c https://iossifovlab.com/distribution/public/studies/genotype-iossifov_2014-${GPF_SERIES}-latest.tar.gz
fi

if ls builds/genotype-comp*.tar.gz  1> /dev/null 2>&1; then
    cp builds/genotype-comp*.tar.gz $WD/genotype-comp-latest.tar.gz
else
    wget -P $WD -c https://iossifovlab.com/distribution/public/studies/genotype-comp-${GPF_SERIES}-latest.tar.gz
fi

if ls builds/phenotype-comp-data*.tar.gz  1> /dev/null 2>&1; then
    cp builds/phenotype-comp-data*.tar.gz $WD/phenotype-comp-data-latest.tar.gz
else
    wget -P $WD -c https://iossifovlab.com/distribution/public/pheno/phenotype-comp-data-${GPF_SERIES}-latest.tar.gz
fi


tar -zxvf $WD/genotype-iossifov_2014-*latest.tar.gz -C $WD
tar -zxvf $WD/genotype-comp-*latest.tar.gz -C $WD
tar -zxvf $WD/phenotype-comp-data-*latest.tar.gz -C $WD

sed -i 's/dae_data_dir =.*/dae_data_dir = "."/' $WD/gpf_remote/DAE.conf
sed -i 's/wd =.*/wd = "."/' $WD/gpf_remote/DAE.conf


# (. $WD/gpf_remote/setenv.sh; cd $WD/iossifov_2014; \
#     simple_study_import.py IossifovWE2014.ped --denovo-file IossifovWE2014.tsv --id iossifov_2014)

#LOCAL_DATA_DIR="$WD/scripts/gpf_remote"

#sed -i -e "s@$LOCAL_DATA_DIR@/data@g" ./gpf_remote/studies/iossifov_2014/iossifov_2014.conf
