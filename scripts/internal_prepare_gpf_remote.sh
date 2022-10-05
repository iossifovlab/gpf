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

cd /code/dae && pip install . 
cd /code/wdae && pip install . 
cd /code/dae_conftests && pip install .


mkdir -p ${DAE_DB_DIR}

tar zxf ${DOWNLOADS}/data-hg19-startup-${GPF_SERIES}*.tar.gz \
    -C ${DAE_DB_DIR} --strip-components=1 \
    --keep-newer-files

# RESET INSTANCE CONF
sed -i \
    s/"^instance_id.*$/instance_id = \"data_hg19_remote\"/"g \
    ${DAE_DB_DIR}/DAE.conf

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


# Import Iossifov 2014
cd ${IMPORT}

tar zxf ${DOWNLOADS}/genotype-iossifov_2014-${GPF_SERIES}*.tar.gz
cd iossifov_2014/
simple_study_import.py --id iossifov_2014 \
    -o ./data_iossifov_2014 \
    --denovo-file IossifovWE2014.tsv \
    IossifovWE2014.ped
cd -

# Enable enrichment in Iossifov 2014
cat <<EOT >> ${DAE_DB_DIR}/studies/iossifov_2014/iossifov_2014.conf

[enrichment]
enabled = true

EOT


# Import comp pheno
cd ${IMPORT}
rm -rf comp-data

tar zxvf ${DOWNLOADS}/phenotype-comp-data-*.tar.gz
cd comp-data

simple_pheno_import.py -p comp_pheno.ped \
    -i instruments/ -d comp_pheno_data_dictionary.tsv -o comp_pheno \
    --regression comp_pheno_regressions.conf

cd -

# Enable comp_pheno for iossifov_2014
sed -i '3i\phenotype_data: comp_pheno' ${DAE_DB_DIR}/studies/iossifov_2014/iossifov_2014.conf


# generate denovo gene sets
generate_denovo_gene_sets.py
