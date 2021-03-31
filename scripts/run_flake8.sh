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


. ${WD}/scripts/version.sh


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
    ${IMAGE_GPF_DEV} -c "/opt/conda/bin/conda run --no-capture-output -n gpf /scripts/internal_run_flake8.sh"
