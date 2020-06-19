#!/bin/bash
# Script intended for running the WDAE django server on the test remote

pip install -e /code/dae
pip install -e /code/wdae

/code/wdae/wdae/wdaemanage.py migrate
/code/wdae/wdae/wdae_create_dev_users.sh
/code/wdae/wdae/wdaemanage.py runserver 0.0.0.0:21010
