#!/bin/bash

set -e

# cleanup
rm -rf ${WD}/gpf_e2e_instance/wdae/*
rm -rf ${WD}/gpf_e2e_instance/phenotype_storage/*
rm -rf ${WD}/gpf_e2e_instance/genotype_storage/*

# setup context
# build_run export DAE_DB_DIR=${WD}/gpf_e2e_instance
# build_run export GRR_DEFINITION_FILE=${WD}/cache/grr_definition.yaml
# build_run grr_cache_repo \
#     --grr ${WD}/cache/grr_definition.yaml \
#     --instance ${WD}/gpf_e2e_instance/gpf_instance.yaml


# import comp data
cd ${WD}/gpf_e2e_instance/input_data/genotypes/comp
rm -rf OUTPUT
import_tools import_project_comp_vcf.yaml -f -vv -j 1
import_tools import_project_comp_denovo.yaml -f -vv -j 1
import_tools import_project_comp_all.yaml -f -vv -j 1

cp comp_vcf.yaml ${WD}/gpf_e2e_instance/studies/comp_vcf
cp comp_denovo.yaml ${WD}/gpf_e2e_instance/studies/comp_denovo
cp comp_all.yaml ${WD}/gpf_e2e_instance/studies/comp_all
cd -

# import iossifov 2014
cd ${WD}/gpf_e2e_instance/input_data/genotypes/iossifov_2014
rm -rf OUTPUT
import_tools import_project.yaml -f -vv -j 1
cp iossifov_2014.yaml ${WD}/gpf_e2e_instance/studies/iossifov_2014/
cd -

# import multi
cd ${WD}/gpf_e2e_instance/input_data/genotypes/multi
rm -rf OUTPUT
import_tools import_project.yaml -f -vv -j 1
cp multi.yaml ${WD}/gpf_e2e_instance/studies/multi/
cd -

# import phenotype comp data
cd ${WD}/gpf_e2e_instance/input_data/phenotypes/comp-data
rm -rf .task-progress .task-log

pheno_import --force -j 1 -v -p comp_pheno.ped \
    -i instruments/ --data-dictionary comp_pheno_data_dictionary.tsv \
    -o ${WD}/gpf_e2e_instance/phenotype_storage/comp_pheno \
    --person-column personId \
    --pheno-id comp_pheno \
    --regression comp_pheno_regressions.yaml

build_pheno_browser -j 1 --force comp_pheno \
    --gpf-instance ${WD}/gpf_e2e_instance/gpf_instance.yaml --no-cache

cp comp_pheno.yaml ${WD}/gpf_e2e_instance/pheno/comp_pheno/comp_pheno.yaml

cd -


# gene profiles generation
generate_gene_profile \
    --genes CHD8,GRIN2B,SHANK2,FLG,CMIP,TBCD,RAPGEF4,RAPGEFL1,RAPGEF1,RAPGEF2,SENP2,SENP3,SENP1,SENP6,SENP8,SENP3-EIF4A1

# generate common reports
generate_common_report
generate_denovo_gene_sets
