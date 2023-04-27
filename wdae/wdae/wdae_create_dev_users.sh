#!/bin/bash

wdaemanage.py user_create admin@iossifovlab.com -p secret -g any_dataset:any_user:admin || true
wdaemanage.py user_create research@iossifovlab.com -p secret -g any_user || true
