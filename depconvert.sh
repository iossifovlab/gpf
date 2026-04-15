#!/bin/bash


grep "=" environment.yml | \
    sed -E "s/\s+-\s+(.+)=(.+)$/\1==\2/g" > requirements.txt

grep "=" gpf_impala_storage/impala-environment.yml | \
    sed -E "s/\s+-\s+(.+)=(.+)$/\1==\2/g" >> requirements.txt

# grep "=" gpf_impala2_storage/impala2-environment.yml | \
#     sed -E "s/\s+-\s+(.+)=(.+)$/\1==\2/g" >> requirements.txt

grep "=" gpf_gcp_storage/gcp-environment.yml | \
    sed -E "s/\s+-\s+(.+)=(.+)$/\1==\2/g" >> requirements.txt
