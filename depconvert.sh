#!/bin/bash


grep "=" environment.yml | \
    sed -E "s/\s+-\s+(.+)=(.+)$/\1==\2/g" > requirements.txt

# grep "=" dev-environment.yml | \
#     sed -E "s/\s+-\s+(.+)=(.+)$/\1==\2/g" >> requirements.txt
