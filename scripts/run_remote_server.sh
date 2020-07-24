#!/bin/bash
# Script intended for running the WDAE django server on the test remote

pip install -e /code/dae
pip install -e /code/wdae

if [ -d "/data/studies/iossifov_2014" ]; then
    echo "Studies found"
else
    echo "Studies missing, importing..."
    /code/dae/dae/tools/simple_study_import.py /study/IossifovWE2014.ped --denovo-file /study/IossifovWE2014.tsv --id iossifov_2014
    echo "Done"
fi

/code/wdae/wdae/wdaemanage.py migrate
/code/wdae/wdae/wdae_create_dev_users.sh
/code/wdae/wdae/wdaemanage.py runserver 0.0.0.0:21010
