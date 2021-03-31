#!/bin/bash

# check this tutorial:
# https://pythonspeed.com/articles/activate-conda-dockerfile/
#

set -e

if [ -z ${WORKSPACE} ];
then
    export WORKSPACE=`pwd`
fi

if [ -z ${WD} ];
then
    export WD=${WORKSPACE}
fi


if [ -z $1 ]; then
    export INTERNAL_RUN="internal_run_gpf.sh"
else
    export INTERNAL_RUN="${1}"
fi 


. ${WD}/scripts/version.sh

. ${WD}/scripts/utils.sh


run_gpf_impala

run_gpf_remote


docker run \
    --rm ${DOCKER_NETWORK_ARG} \
    --link ${CONTAINER_GPF_IMPALA}:impala \
    --link ${CONTAINER_GPF_REMOTE}:gpfremote \
    --entrypoint /bin/bash \
    -v ${WD}:/code \
    -v ${DAE_DB_DIR}:/data \
    -v ${IMPORT}:/import \
    -v ${DOWNLOADS}:/downloads \
    -v ${SCRIPTS}:/scripts \
    -e BUILD_NUMBER=${BUILD_NUMBER} \
    -e BRANCH_NAME=${BRANCH_NAME} \
    -e GPF_VERSION=${GPF_VERSION} \
    -e GPF_TAG=${GPF_TAG} \
    -e WORKSPACE="/" \
    -e WD="/" \
    -e DAE_DB_DIR="/data" \
    -e TEST_REMOTE_HOST=gpfremote \
    -e DAE_HDFS_HOST="impala" \
    -e DAE_IMPALA_HOST="impala" \
    -e RUN_WHAT=${2} \
    ${IMAGE_GPF_DEV} -c "/opt/conda/bin/conda run --no-capture-output -n gpf /scripts/${INTERNAL_RUN}"
