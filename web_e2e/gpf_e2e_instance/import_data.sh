#!/bin/bash

set -e

# Resolve INSTANCE_DIR to the directory holding this script,
# regardless of CWD. This makes the script location-
# independent: works whether the instance is mounted at /data
# in the e2e backend container or sits inside a dev checkout.
INSTANCE_DIR="$(cd "$(dirname "$0")" && pwd)"

export DAE_DB_DIR="${INSTANCE_DIR}"

# Apply Django migrations first so the wdae user/permission
# tables exist before the user_create calls at the bottom. The
# data imports below don't touch the Django ORM (storage is
# duckdb/parquet under genotype_storage/ + phenotype_storage/),
# so this single one-shot covers schema + data + users.
wdaemanage migrate --noinput

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

# tb-nxl: per-worker user pool. utils.loginWorkerUser(page) picks
# e2e_worker_<TEST_PARALLEL_INDEX> so each Playwright worker writes to
# its own user row — no cross-spec admin-row sharing under workers=16.
# Pool size matches Playwright's `workers` (single source of truth:
# E2E_WORKER_COUNT, plumbed via web_infra/compose-jenkins.yaml).
# any_dataset:any_user (no `admin` group) is deliberate: an accidental
# /management write hits 403 instead of stomping shared state — see
# tb-nxl Q5 for the structural reasoning. Tests that genuinely need the
# admin group go through tests/_literal_admin.ts loginLiteralAdmin and
# are confined to user-management.spec.ts (CI grep enforced).
e2e_worker_count="${E2E_WORKER_COUNT:-16}"
for i in $(seq 0 $((e2e_worker_count - 1))); do
    wdaemanage user_create "e2e_worker_${i}@iossifovlab.com" \
        -p secret -g any_dataset:any_user || true
done

# Register the SPA's OAuth2 application. The SPA's log-in
# button (web_ui/src/app/users/users.component.ts) issues a
# PKCE authorization-code request with client_id=gpfjs and
# redirect_uri=<origin>/login; users_api.get_default_application
# expects exactly that record (settings.DEFAULT_OAUTH_APPLICATION_CLIENT
# = "gpfjs"). createapplication has no --update mode, so guard
# with `|| true` for re-runs against a populated DB.
#
# --skip-authorization bypasses the consent screen — the e2e
# tests log in non-interactively, they don't drive the
# "Authorize gpfjs" form. --no-hash-client-secret is fine for
# a public PKCE client (the secret isn't used). redirect-uris
# covers both the CI compose hostname (frontend) and the
# loopback URL local devs would hit.
wdaemanage createapplication \
    --client-id gpfjs \
    --name gpfjs \
    --skip-authorization \
    --no-hash-client-secret \
    --redirect-uris "http://frontend/login http://localhost:8080/gpf/login http://127.0.0.1:8080/gpf/login http://localhost:8080/login http://127.0.0.1:8080/login http://localhost:4200/login" \
    public authorization-code || true
