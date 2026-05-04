#!/bin/bash

set -e

# Resolve INSTANCE_DIR to the directory holding this script,
# regardless of CWD. This makes the script location-
# independent: works whether the instance is mounted at /data
# in the e2e backend container or sits inside a dev checkout.
INSTANCE_DIR="$(cd "$(dirname "$0")" && pwd)"

export DAE_DB_DIR="${INSTANCE_DIR}"

# cleanup
rm -rf "${INSTANCE_DIR}"/wdae/*
rm -rf "${INSTANCE_DIR}"/phenotype_storage/*
rm -rf "${INSTANCE_DIR}"/genotype_storage/*
rm -rf "${INSTANCE_DIR}"/gpdb.duckdb

# import comp data
cd "${INSTANCE_DIR}"/input_data/genotypes/comp
rm -rf OUTPUT
import_tools import_project_comp_vcf.yaml -f -vv -j 1
import_tools import_project_comp_denovo.yaml -f -vv -j 1
import_tools import_project_comp_all.yaml -f -vv -j 1

cd -

# import iossifov 2014
cd "${INSTANCE_DIR}"/input_data/genotypes/iossifov_2014
rm -rf OUTPUT
import_tools import_project.yaml -f -vv -j 1
cd -

# import multi
cd "${INSTANCE_DIR}"/input_data/genotypes/multi
rm -rf OUTPUT
import_tools import_project.yaml -f -vv -j 1
cd -

# import helloworld data
cd "${INSTANCE_DIR}"/input_data/genotypes/helloworld
rm -rf OUTPUT
import_genotypes denovo_helloworld.yaml -f -vv -j 1
import_genotypes vcf_helloworld.yaml -f -vv -j 1

cd -

cd "${INSTANCE_DIR}"/input_data/phenotypes/helloworld
rm -rf .task-progress .task-log work
import_phenotypes import_project.yaml -f -vv -j 1

build_pheno_browser -j 1 --force pheno_helloworld \
    --gpf-instance "${INSTANCE_DIR}"/gpf_instance.yaml

cd -

# gene profiles generation
generate_gene_profile \
    --genes CHD8,GRIN2B,SHANK2,FLG,CMIP,TBCD,RAPGEF4,RAPGEFL1,RAPGEF1,RAPGEF2,SENP2,SENP3,SENP1,SENP6,SENP8,SENP3-EIF4A1

# generate common reports
generate_common_report
generate_denovo_gene_sets

# create dev users for the e2e suite (idempotent: || true so reruns
# don't fail once the users already exist)
wdaemanage user_create admin@iossifovlab.com -p secret -g any_dataset:any_user:admin || true
wdaemanage user_create research@iossifovlab.com -p secret -g any_user || true
wdaemanage user_create user_comp_vcf@iossifovlab.com -p secret -g any_user || true
wdaemanage user_create user_comp_genotypes@iossifovlab.com -p secret -g any_user || true
wdaemanage user_create user_all_genotypes@iossifovlab.com -p secret -g any_user || true
wdaemanage user_create user_iossifov_2014@iossifovlab.com -p secret -g any_user || true
