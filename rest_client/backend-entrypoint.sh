#!/usr/bin/bash

for d in /wd/dae /wd/wdae /wd/rest_client; do
    cd ${d};
    /opt/conda/bin/conda run --no-capture-output -n gpf pip install -e .
done

rm -rf /wd/rest_client/tmp
mkdir -p /wd/rest_client/tmp

/opt/conda/bin/conda run --no-capture-output -n gpf \
    python /wd/rest_client/setup_testing_remote.py

export GRR_DEFINITION_FILE="/wd/rest_client/tmp/grr_definition.yaml"

/opt/conda/bin/conda run --no-capture-output -n gpf \
    wdaemanage migrate
/opt/conda/bin/conda run --no-capture-output -n gpf \
    wdaemanage user_create admin@iossifovlab.com -p secret -g any_dataset:any_user:admin
/opt/conda/bin/conda run --no-capture-output -n gpf \
    wdaemanage user_create research@iossifovlab.com -p secret -g any_user

/opt/conda/bin/conda run -n gpf \
    wdaemanage createapplication \
        confidential client-credentials \
        --user 1 \
        --name "remote federation testing app" \
        --client-id federation \
        --client-secret secret

/opt/conda/bin/conda run -n gpf \
    wdaemanage createapplication \
        confidential client-credentials \
        --user 2 \
        --name "remote federation testing app 2" \
        --client-id federation2 \
        --client-secret secret \
        --skip-authorization

while true; do
    /opt/conda/bin/conda run --no-capture-output -n gpf \
        wdaemanage runserver backend:21011
    sleep 10
done
