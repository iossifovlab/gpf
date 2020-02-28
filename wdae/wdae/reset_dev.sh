#!/bin/bash

rm -rf wdae.sql
rm -rf wdae_django_pre.cache
rm -rf wdae_django_default.cache

wdaemanage.py migrate
./wdae_create_dev_users.sh

