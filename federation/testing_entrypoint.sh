#!/usr/bin/bash

for d in /wd/dae /wd/wdae; do
    cd ${d};
    /opt/conda/bin/conda run --no-capture-output -n gpf pip install -e .
done

rm -rf /wd/federation/tmp
mkdir /wd/federation/tmp

/opt/conda/bin/conda run --no-capture-output -n gpf \
    python /wd/federation/setup_testing_remote.py

export GRR_DEFINITION_FILE="/wd/federation/tmp/grr_definiton.yaml"

/opt/conda/bin/conda run --no-capture-output -n gpf \
    /wd/wdae/wdae/wdaemanage.py migrate
/opt/conda/bin/conda run --no-capture-output -n gpf \
    /wd/wdae/wdae/wdae_create_dev_users.sh
/opt/conda/bin/conda run -n gpf \
    /wd/wdae/wdae/wdae_create_dev_federation_app.sh

while true; do
    /opt/conda/bin/conda run --no-capture-output -n gpf \
        /wd/wdae/wdae/wdaemanage.py runserver 0.0.0.0:21010
    sleep 10
done
