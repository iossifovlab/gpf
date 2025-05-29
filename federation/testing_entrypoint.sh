#!/usr/bin/bash

for d in /wd/dae /wd/wdae; do
    cd ${d};
    /opt/conda/bin/conda run --no-capture-output -n gpf pip install -e .
done

rm -rf /wd/federation/tmp
mkdir /wd/federation/tmp

/opt/conda/bin/conda run --no-capture-output -n gpf \
    python /wd/federation/setup_testing_remote.py

export GRR_DEFINITION_FILE="/wd/federation/tmp/grr_definition.yaml"

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

while true; do
    /opt/conda/bin/conda run --no-capture-output -n gpf \
        wdaemanage runserver 0.0.0.0:21010
    sleep 10
done
