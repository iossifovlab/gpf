#!/bin/bash

rm -rf $DAE_DB_DIR/wdae/wdae.sql
rm -rf $DAE_DB_DIR/wdae/wdae_django_pre.cache
rm -rf $DAE_DB_DIR/wdae/wdae_django_default.cache

wdaemanage.py migrate
./wdae_create_dev_users.sh
./wdae_create_dev_gpfjs_app.sh
