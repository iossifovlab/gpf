#!/bin/bash

rm -rf wdae.sql
rm -rf wdae_django_pre.cache
rm -rf wdae_django_default.cache

python manage.py migrate
./create_dev_users.sh

