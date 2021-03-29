#!/bin/bash

set -e

if [ -z ${WORKSPACE} ];
then
    export WORKSPACE=`pwd`
fi

if [ -z ${WD} ];
then
    export WD=${WORKSPACE}
fi



. ${WD}/scripts/version.sh


cd ${WD}
docker build . -f ${WD}/Dockerfile -t ${IMAGE_GPF_DEV}

sed -i "s/localhost/impala/" ${WD}/dae_conftests/dae_conftests/tests/fixtures/DAE.conf

if [ -z ${1} ];
then
    ${SCRIPTS}/run_gpf_dev.sh internal_run_dae_tests.sh
    # ${SCRIPTS}/run_gpf_dev.sh internal_run_wdae_tests.sh
else
    ${SCRIPTS}/run_gpf_dev.sh internal_run_tests.sh ${1}
fi

cd ${WD}
git checkout dae_conftests/dae_conftests/tests/fixtures/DAE.conf
cd -