#!/bin/bash

rm -rf wdae.sql

# python manage.py syncdb
python manage.py migrate

python manage.py devusers


