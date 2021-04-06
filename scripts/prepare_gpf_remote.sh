#!/bin/bash

# check this tutorial:
# https://pythonspeed.com/articles/activate-conda-dockerfile/
#

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

. ${WD}/scripts/utils.sh


run_gpf_impala


if [ ! -d ${DAE_DB_DIR_REMOTE} ];
then

    echo "preparing DAE_DB_DIR_REMOTE: ${DAE_DB_DIR_REMOTE}"
    mkdir -p ${DAE_DB_DIR_REMOTE}


    docker run \
        --rm ${DOCKER_NETWORK_ARG} \
        --link ${CONTAINER_GPF_IMPALA}:impala \
        --entrypoint /bin/bash \
        -v ${WD}:/code \
        -v ${DAE_DB_DIR_REMOTE}:/data \
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
        ${IMAGE_GPF_DEV} -c "/opt/conda/bin/conda run --no-capture-output -n gpf /scripts/internal_prepare_gpf_remote.sh"

fi
