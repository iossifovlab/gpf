#!/usr/bin/env bash

set -e

if [ -z ${GS} ]; then
    export GS="genotype_impala"
fi 

if [ -z ${WORKSPACE} ];
then
    export WORKSPACE=`pwd`
fi

if [ -z ${WD} ];
then
    export WD=${WORKSPACE}
fi

echo "WORKSPACE                     : ${WORKSPACE}"
echo "WD                            : ${WD}"


. ${WD}/scripts/env.sh 

echo "DAE_DB_DIR                    : ${DAE_DB_DIR}"

for d in /code/dae /code/wdae /code/dae_conftests; do
    cd ${d}
    pip install -e .
done

/code/wdae/wdae/wdaemanage.py migrate
/code/wdae/wdae/wdae_create_dev_users.sh

/code/wdae/wdae/wdaemanage.py runserver 0.0.0.0:21010
