#!/usr/bin/env bash

set -e


if [ -z ${WORKSPACE} ];
then
    export WORKSPACE=`pwd`
fi

if [ -z ${WD} ];
then
    export WD=${WORKSPACE}
fi

echo "WORKSPACE                     : ${WORKSPACE}"
echo "WD                            : ${WD}"


. ${WD}/scripts/env.sh 

echo "DAE_DB_DIR                    : ${DAE_DB_DIR}"

ls -la ${DOWNLOADS}

tar zxf ${DOWNLOADS}/data-hg19-startup-${GPF_SERIES}*.tar.gz \
    -C ${DAE_DB_DIR} --strip-components=1 \
    --keep-newer-files

# RESET INSTANCE CONF

sed -i \
    s/"^impala\.host.*$/impala.hosts = \[\"impala\"\]/"g \
    ${DAE_DB_DIR}/DAE.conf

sed -i \
    s/"^hdfs\.host.*$/hdfs.host = \"impala\"/"g \
    ${DAE_DB_DIR}/DAE.conf

# CLEAN UP
rm -rf ${DAE_DB_DIR}/studies/*
rm -rf ${DAE_DB_DIR}/pheno/*
rm -rf ${DAE_DB_DIR}/wdae/wdae.sql

## SETUP directory structure
mkdir -p ${DAE_DB_DIR}/genomic-scores-hg19
mkdir -p ${DAE_DB_DIR}/genomic-scores-hg38

mkdir -p ${DAE_DB_DIR}/wdae
