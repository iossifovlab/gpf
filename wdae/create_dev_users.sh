#!/bin/bash

./manage.py user_create admin@iossifovlab.com -p secret -g any_dataset:superuser
./manage.py user_create research@iossifovlab.com -p secret
