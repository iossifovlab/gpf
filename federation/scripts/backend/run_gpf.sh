#!/bin/bash
set -euo pipefail

# Backend entrypoint for the federation integration test stack. Seeds a
# t4c8 GPF instance under /workspace/federation/tmp, runs the wdae
# migrations, creates the test users + OAuth client, then serves wdae on
# 0.0.0.0:21010 (the federation runner container reaches it via
# TEST_REMOTE_HOST=http://backend:21010).

mkdir -p /workspace/federation/tmp
rm -rf /workspace/federation/tmp/*
python /workspace/federation/setup_testing_remote.py

export GRR_DEFINITION_FILE=/workspace/federation/tmp/grr_definition.yaml
export DAE_DB_DIR=/workspace/federation/tmp/gpf_instance

wdaemanage migrate --noinput
wdaemanage user_create admin@iossifovlab.com -p secret -g any_dataset:admin
wdaemanage user_create researcher@iossifovlab.com -p secret -g any_dataset:admin
wdaemanage createapplication \
    confidential client-credentials \
    --user 1 \
    --name "remote federation testing app" \
    --client-id federation \
    --client-secret secret

exec wdaemanage runserver --noreload 0.0.0.0:21010
