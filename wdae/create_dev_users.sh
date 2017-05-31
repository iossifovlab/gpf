#!/bin/bash

python manage.py user_create admin@iossifovlab.com -p secret -g superuser
python manage.py user_create research@iossifovlab.com -p secret
python manage.py user_create vip@iossifovlab.com -p secret
python manage.py user_create ssc@iossifovlab.com -p secret
