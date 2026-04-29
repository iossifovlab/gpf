#!/bin/bash
set -euo pipefail

# Backend entrypoint for the rest_client integration test stack. Seeds a
# t4c8 GPF instance under /workspace/rest_client/tmp, runs the wdae
# migrations, creates the test users + OAuth clients, then serves wdae
# on 0.0.0.0:21011 (the rest_client runner container reaches it via
# --url http://backend:21011).

mkdir -p /workspace/rest_client/tmp
rm -rf /workspace/rest_client/tmp/*
python /workspace/rest_client/setup_testing_remote.py

export GRR_DEFINITION_FILE=/workspace/rest_client/tmp/grr_definition.yaml
export DAE_DB_DIR=/workspace/rest_client/tmp/gpf_instance

wdaemanage migrate --noinput
wdaemanage user_create admin@iossifovlab.com -p secret \
    -g any_dataset:any_user:admin
wdaemanage user_create research@iossifovlab.com -p secret -g any_user
wdaemanage createapplication \
    confidential client-credentials \
    --user 1 \
    --name "remote federation testing app" \
    --client-id federation \
    --client-secret secret
wdaemanage createapplication \
    confidential client-credentials \
    --user 2 \
    --name "remote federation testing app 2" \
    --client-id federation2 \
    --client-secret secret \
    --skip-authorization

exec wdaemanage runserver --noreload 0.0.0.0:21011
