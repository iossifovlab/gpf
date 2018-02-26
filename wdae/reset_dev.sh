#!/bin/bash

rm -rf wdae.sql
rm -rf wdae_django_pre.cache

python manage.py migrate
./create_dev_users.sh
python manage.py recompute

