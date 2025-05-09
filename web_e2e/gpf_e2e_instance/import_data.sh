#!/bin/bash

set -e

# cleanup
rm -rf ${WD}/gpf_e2e_instance/wdae/*
rm -rf ${WD}/gpf_e2e_instance/phenotype_storage/*
rm -rf ${WD}/gpf_e2e_instance/genotype_storage/*
rm -rf ${WD}/gpf_e2e_instance/gpdb.duckdb

# import comp data
cd ${WD}/gpf_e2e_instance/input_data/genotypes/comp
rm -rf OUTPUT
import_tools import_project_comp_vcf.yaml -f -vv -j 1
import_tools import_project_comp_denovo.yaml -f -vv -j 1
import_tools import_project_comp_all.yaml -f -vv -j 1

cd -

# import iossifov 2014
cd ${WD}/gpf_e2e_instance/input_data/genotypes/iossifov_2014
rm -rf OUTPUT
import_tools import_project.yaml -f -vv -j 1
cd -

# import multi
cd ${WD}/gpf_e2e_instance/input_data/genotypes/multi
rm -rf OUTPUT
import_tools import_project.yaml -f -vv -j 1
cd -

# import helloworld data
cd ${WD}/gpf_e2e_instance/input_data/genotypes/helloworld
rm -rf OUTPUT
import_genotypes denovo_helloworld.yaml -f -vv -j 1
import_genotypes vcf_helloworld.yaml -f -vv -j 1

cd -

cd ${WD}/gpf_e2e_instance/input_data/phenotypes/helloworld
rm -rf .task-progress .task-log work
import_phenotypes import_project.yaml -f -vv -j 1

build_pheno_browser -j 1 --force pheno_helloworld \
    --gpf-instance ${WD}/gpf_e2e_instance/gpf_instance.yaml \
    --no-cache

cd -

# gene profiles generation
generate_gene_profile \
    --genes CHD8,GRIN2B,SHANK2,FLG,CMIP,TBCD,RAPGEF4,RAPGEFL1,RAPGEF1,RAPGEF2,SENP2,SENP3,SENP1,SENP6,SENP8,SENP3-EIF4A1

# generate common reports
generate_common_report
generate_denovo_gene_sets
