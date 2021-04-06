#!/usr/bin/env bash

set -e

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


cd /code/dae_conftests
py.test -v --reimport --no-cleanup dae_conftests/tests/

cd /code/dae
py.test -v --no-cleanup dae/gene/tests/test_denovo_gene_sets_db.py
py.test -v --no-cleanup dae/backends/tests/test_cnv_variants.py::test_cnv_impala
