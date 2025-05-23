#!/bin/bash

wdaemanage.py user_create admin@iossifovlab.com -p secret -g any_dataset:any_user:admin || true
wdaemanage.py user_create research@iossifovlab.com -p secret -g any_user || true
wdaemanage.py user_create user_comp_vcf@iossifovlab.com -p secret -g any_user || true
wdaemanage.py user_create user_comp_genotypes@iossifovlab.com -p secret -g any_user || true
wdaemanage.py user_create user_all_genotypes@iossifovlab.com -p secret -g any_user || true
wdaemanage.py user_create user_iossifov_2014@iossifovlab.com -p secret -g any_user || true