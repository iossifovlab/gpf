#!/bin/bash

rm -rf wdae.sql
rm -rf wdae_django_pre.cache

python manage.py syncdb
python manage.py migrate

python manage.py devusers

