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

preview_columns = ["family", "variant", "genotype", "effect", "weights", "mpc_cadd", "freq", "pheno"]

[genotype_browser.column_groups]
pheno.name = "Measures"
pheno.columns = ["pheno_age", "pheno_viq"]


[genotype_browser.columns.phenotype]
pheno_age.role = "prb"
pheno_age.source = "i1.age"
pheno_age.name = "Age"

pheno_iq.role = "prb"
pheno_iq.source = "i1.iq"
pheno_iq.name = "Iq"


EOT

cat <<EOT >> ${DAE_DB_DIR}/studies/iossifov_2014/iossifov_2014.conf

[enrichment]
enabled = true

EOT

mkdir -p ${DAE_DB_DIR}/datasets/COMP_genotypes
mkdir -p ${DAE_DB_DIR}/datasets/ALL_genotypes

cat <<EOT >> ${DAE_DB_DIR}/datasets/COMP_genotypes/COMP_genotypes.conf

id = "COMP_genotypes"
name = "COMP Genotypes"

studies = [
	"comp_denovo", 
	"comp_vcf", 
]

study_type = ["WG"]
has_complex = true
enabled = true

[genotype_browser]

has_present_in_child = true
has_present_in_parent = true
has_pedigree_selector = false

variant_types = ["sub", "ins", "del", "complex"]
selected_variant_types = ["sub", "ins", "del", "complex"]

[denovo_gene_sets]
enabled = false

[common_report]
enabled = false


EOT

cat <<EOT >> ${DAE_DB_DIR}/datasets/ALL_genotypes/ALL_genotypes.conf

id = "ALL_genotypes"
name = "ALL Genotypes"

studies = [
	"comp_all", 
	"COMP_genotypes",
	"multi", 
	"iossifov_2014",
]

study_type = ["WG"]
has_complex = true
enabled = true

[genotype_browser]

has_present_in_child = true
has_present_in_parent = true
has_pedigree_selector = false

variant_types = ["sub", "ins", "del", "complex"]
selected_variant_types = ["sub", "ins", "del", "complex"]

[denovo_gene_sets]
enabled = false

[common_report]
enabled = false


EOT


cat <<EOT >> ${DAE_DB_DIR}/DAE.conf

[autism_gene_tool_config]
conf_file = "%(wd)s/autismGeneTool.conf"

EOT

cat << EOT >> ${DAE_DB_DIR}/autismGeneTool.conf


default_dataset = "ALL_genotypes"

[[gene_sets]]
category = "autism_gene_sets"
display_name = "Autism Gene Sets"
sets = [
    { set_id="autism candidates from Iossifov PNAS 2015", collection_id = "main" },
    { set_id="autism candidates from Sanders Neuron 2015", collection_id = "main" },
]

[[gene_sets]]
category = "relevant_gene_sets"
display_name = "Relevant Gene Sets"

sets = [
    { set_id="CHD8 target genes", collection_id="main" },
    { set_id="chromatin modifiers", collection_id="main" },
    { set_id="essential genes", collection_id="main" },
    { set_id="FMRP Darnell", collection_id="main" },
]

[[genomic_scores]]
category = "autism_scores"
display_name = "Autism Scores"
scores = [
    {score_name="SFARI_gene_score", format="%%s"},
]

[[genomic_scores]]
category = "protection_scores"
display_name = "Protection Scores"
scores = [
    {score_name="RVIS_rank", format="%%s"},
    {score_name="LGD_rank", format="%%s"},
    {score_name="pLI_rank", format="%%s"},
    {score_name="pRec_rank", format="%%s"},
]


[datasets.iossifov_2014]
effects = ["LGDS", "missense", "intron"]
[[datasets.iossifov_2014.person_sets]]
set_name="affected"
collection_name="status"
[[datasets.iossifov_2014.person_sets]]
set_name="unaffected"
collection_name="status"

EOT

generate_autism_gene_profile.py -VV --config-genes
generate_agp_cache_table.py -VV


echo "done prepartion of DAE_DB_DIR (${DAE_DB_DIR})..."