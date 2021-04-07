#!/bin/bash

set -e

if [ -z $1 ]; then
    export GS="genotype_impala"
else
    export GS="${1}"
fi 

if [ -z ${WORKSPACE} ];
then
    export WORKSPACE=`pwd`
fi

if [ -z ${WD} ];
then
    export WD=${WORKSPACE}
fi

. ${WD}/scripts/version.sh


echo "GS                            : ${GS}"


docker pull seqpipe/seqpipe-node-base:latest

docker run --rm \
    --ipc=host \
    --entrypoint /bin/bash \
    --network ${NETWORK} \
    --name ${CONTAINER_E2E_TESTS} \
    --link ${CONTAINER_GPF_IMPALA}:impala \
    --link ${CONTAINER_GPF_DEV}:${CONTAINER_GPF_DEV} \
    -v ${DATA}:/data \
    -v ${DOWNLOADS}:/downloads \
    -v ${SCRIPTS}:/scripts \
    -v ${WD}:/e2e \
    -v ${RESULTS}:/results \
    -e "WD=/" \
    -e "WORKSPACE=/" \
    -e "E2E=/e2e" \
    -e "GPF_TAG=${GPF_TAG}" \
    -e "BUILD_NUMBER=${BUILD_NUMBER}" \
    -e "GS=${GS}" \
    -e "CONTAINER_GPF_DEV=${CONTAINER_GPF_DEV}" \
    seqpipe/seqpipe-node-base:latest /scripts/internal_run_gpf_e2e.sh


