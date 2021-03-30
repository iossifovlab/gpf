#!/bin/bash

# check this tutorial:
# https://pythonspeed.com/articles/activate-conda-dockerfile/
#

set -e

if [ -z $1 ]; then
    export GS="genotype_impala"
else
    export GS="${1}"
fi 

if [ -z ${WORKSPACE} ];
then
    export WORKSPACE=`pwd`
fi

if [ -z ${WD} ];
then
    export WD=${WORKSPACE}
fi

. ${WD}/scripts/version.sh

mkdir -p ${DOWNLOADS}

# download data hg19 startup
if ls ${DOWNLOADS}/data-hg19-startup-${GPF_SERIES}*.tar.gz 1> /dev/null 2>&1; then
    echo "dataset data-hg19-startup-${GPF_SERIES}*.tar.gz found into ${DOWNLOADS}... nothing to download..."
else
    wget -P ${DOWNLOADS} -c https://iossifovlab.com/distribution/public/data-hg19-startup-${GPF_SERIES}-latest.tar.gz
fi

if ls ${DOWNLOADS}/genotype-iossifov_2014-${GPF_SERIES}*.tar.gz 1> /dev/null 2>&1; then
    echo "dataset genotype-iossifov_2014-${GPF_SERIES}*.tar.gz found into ${DOWNLOADS}... nothing to download..."
else
    wget -P ${DOWNLOADS} -c https://iossifovlab.com/distribution/public/studies/genotype-iossifov_2014-${GPF_SERIES}-latest.tar.gz
fi

if ls ${DOWNLOADS}/genotype-comp-${GPF_SERIES}*.tar.gz  1> /dev/null 2>&1; then
    echo "dataset genotype-comp-${GPF_SERIES}*.tar.gz found into ${DOWNLOADS}... nothing to download..."
else
    wget -P ${DOWNLOADS} -c https://iossifovlab.com/distribution/public/studies/genotype-comp-${GPF_SERIES}-latest.tar.gz
fi

if ls ${DOWNLOADS}/genotype-multi-${GPF_SERIES}*.tar.gz  1> /dev/null 2>&1; then
    echo "dataset genotype-multi-${GPF_SERIES}*.tar.gz found into ${DOWNLOADS}... nothing to download..."
else
    wget -P ${DOWNLOADS} -c https://iossifovlab.com/distribution/public/studies/genotype-multi-${GPF_SERIES}-latest.tar.gz
fi

if ls ${DOWNLOADS}/phenotype-comp-data-${GPF_SERIES}*.tar.gz  1> /dev/null 2>&1; then
    echo "dataset phenotype-comp-data-${GPF_SERIES}*.tar.gz found into ${DOWNLOADS}... nothing to download..."
else
    wget -P ${DOWNLOADS} -c https://iossifovlab.com/distribution/public/pheno/phenotype-comp-data-${GPF_SERIES}-latest.tar.gz
fi

