#!/usr/bin/env bash

set -e

if [ -z ${GS} ]; then
    export GS="genotype_impala"
fi 

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

echo "GS                            : ${GS}"
echo "DAE_DB_DIR                    : ${DAE_DB_DIR}"


tar zxvf ${DOWNLOADS}/data-hg19-startup-${GPF_SERIES}*.tar.gz \
    -C ${DAE_DB_DIR} --strip-components=1 \
    --keep-newer-files


# RESET INSTANCE CONF

sed -i \
    s/"^instance_id.*$/instance_id = \"data_hg19_startup_${GS}\"/"g \
    ${DAE_DB_DIR}/DAE.conf

sed -i \
    s/"^impala\.db.*$/impala.db = \"data_hg19_startup_${GS}\"/"g \
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

# IMPORT COMP STUDIES

cd ${IMPORT}
tar zxvf ${DOWNLOADS}/genotype-comp-${GPF_SERIES}*.tar.gz
cd comp

simple_study_import.py --id comp_vcf \
    -o ./data_comp_vcf \
    --vcf-files comp.vcf \
    --genotype-storage ${GS} \
    comp.ped

simple_study_import.py --id comp_denovo \
    -o ./data_comp_denovo \
    --denovo-file comp.tsv \
    --genotype-storage ${GS} \
    comp.ped

simple_study_import.py --id comp_all \
    -o ./data_comp_all \
    --denovo-file comp.tsv \
    --vcf-files comp.vcf \
    --genotype-storage ${GS} \
    comp.ped
cd -

cd ${IMPORT}

tar zxf ${DOWNLOADS}/genotype-iossifov_2014-${GPF_SERIES}*.tar.gz
cd iossifov_2014/
simple_study_import.py --id iossifov_2014 \
    -o ./data_iossifov_2014 \
    --denovo-file IossifovWE2014.tsv \
    --genotype-storage ${GS} \
    IossifovWE2014.ped
cd -

cd ${IMPORT}

tar zxf ${DOWNLOADS}/genotype-multi-${GPF_SERIES}*.tar.gz
cd multi/
simple_study_import.py --id multi \
    -o ./data_multi \
    --vcf-files multi.vcf \
    --genotype-storage ${GS} \
    multi.ped
cd -
echo "import of <multi> study done"

cd ${IMPORT}

tar zxvf ${DOWNLOADS}/phenotype-comp-data-*.tar.gz
cd comp-data

simple_pheno_import.py -p comp_pheno.ped \
    -i instruments/ -d comp_pheno_data_dictionary.tsv -o comp_pheno \
    --regression comp_pheno_regressions.conf

cd -


sed -i \
    '1s;^;phenotype_data = "comp_pheno"\n\nphenotype_browser = true\n\nphenotype_tool = true\n;' \
    ${DAE_DB_DIR}/studies/comp_all/comp_all.conf

cat <<EOT >> ${DAE_DB_DIR}/studies/comp_all/comp_all.conf

family_filters.sample_continuous_filter.name = "Sample Filter Name"
family_filters.sample_continuous_filter.source_type = "continuous"
family_filters.sample_continuous_filter.from = "phenodb"
family_filters.sample_continuous_filter.filter_type = "multi"
family_filters.sample_continuous_filter.role = "prb"


selected_pheno_column_values = ["pheno"]

pheno.pheno.name = "Measures"
pheno.pheno.slots = [
    {role = "prb", source = "i1.age", name = "Age"},
    {role = "prb", source = "i1.iq", name = "Iq"}
]

preview_columns = ["family", "variant", "genotype", "effect", "weights", "mpc_cadd", "freq", "pheno"]

EOT

cat <<EOT >> ${DAE_DB_DIR}/studies/iossifov_2014/iossifov_2014.conf

[enrichment]
enabled = true

EOT


cat <<EOT >> ${DAE_DB_DIR}/DAE.conf

[autism_gene_tool_config]
conf_file = "%(wd)s/autismGeneTool.conf"

EOT

cat << EOT >> ${DAE_DB_DIR}/autismGeneTool.conf

gene_sets = [
    "autism candidates from Sanders Neuron 2015",
    "synaptic clefts inhibitory",
    "topotecan downreg genes",
    "postsynaptic inhibition",
]

default_dataset = "iossifov_2014"

protection_scores = ["SFARI_gene_score", "RVIS_rank", "RVIS"]
autism_scores = ["SFARI_gene_score", "RVIS_rank", "RVIS"]

[datasets.iossifov_2014]
effects = ["LGDS", "missense", "intron"]
[[datasets.iossifov_2014.person_sets]]
set_name="affected"
collection_name="status"
[[datasets.iossifov_2014.person_sets]]
set_name="unaffected"
collection_name="status"

EOT

generate_autism_gene_profile.py -VV
generate_agp_cache_table.py -VV


echo "done prepartion of DAE_DB_DIR (${DAE_DB_DIR})..."