#!/bin/bash

# Absolute path to this script, e.g. /home/user/bin/foo.sh
SCRIPT=$(readlink -f "$0")
# Absolute path this script is in, thus /home/user/bin
SCRIPTPATH=$(dirname "$SCRIPT")

rm -rf $DAE_DB_DIR/wdae/wdae.sql
rm -rf $DAE_DB_DIR/wdae/wdae_django_pre.cache
rm -rf $DAE_DB_DIR/wdae/wdae_django_default.cache

wdaemanage.py migrate
$SCRIPTPATH/wdae_create_dev_users.sh
$SCRIPTPATH/wdae_create_dev_gpfjs_app.sh
$SCRIPTPATH/wdae_create_dev_federation_app.sh
