#!/usr/bin/bash

mkdir /wd/federation/tmp
mkdir /wd/federation/tmp/instance
mkdir /wd/federation/tmp/grrCache

cat >> /wd/federation/tmp/grr_definition.yaml << EOT
id: "remote"
type: "directory"
directory: "/wd/federation/tmp/grrCache"
EOT

/opt/conda/bin/conda run --no-capture-output -n gpf \
    /wd/federation/setup_testing_remote.py

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

rm -rf /wd/federation/tmp
