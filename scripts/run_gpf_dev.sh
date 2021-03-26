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



export HAS_NETWORK=`docker network ls | grep ${NETWORK} | sed -e "s/\s\{2,\}/\t/g" | cut -f 1`

if [[ -z $HAS_NETWORK ]]; then
    echo "going to create docker network ${NETWORK}"
    docker network create -d bridge ${NETWORK} || true
fi


echo "Looking for gpf impala container: ${CONTAINER_GPF_IMPALA}"
export HAS_GPF_IMPALA=`docker ps -a | grep ${CONTAINER_GPF_IMPALA} | sed -e "s/\s\{2,\}/\t/g" | cut -f 1`
echo "Impala container: <${HAS_GPF_IMPALA}>"
if [[ -z $HAS_GPF_IMPALA ]]; then
    # create gpf_impala docker container

    echo "going to create gpf impala container ${CONTAINER_GPF_IMPALA}"
    docker pull seqpipe/seqpipe-docker-impala:latest
    docker create \
        --name ${CONTAINER_GPF_IMPALA} \
        --network ${NETWORK} \
        --hostname impala \
        seqpipe/seqpipe-docker-impala:latest

fi

export HAS_RUNNING_GPF_IMPALA=`docker ps | grep ${CONTAINER_GPF_IMPALA} | sed -e "s/\s\{2,\}/\t/g" | cut -f 1`

echo "Has running impala: <${HAS_RUNNING_GPF_IMPALA}>"
if [[ -z $HAS_RUNNING_GPF_IMPALA ]]; then
    echo "starting gpf_impala container ${CONAINER_GPF_IMPALA}..."
    docker start ${CONTAINER_GPF_IMPALA}
fi

echo "waiting gpf_impala container..."
docker exec ${CONTAINER_GPF_IMPALA} /wait-for-it.sh -h localhost -p 21050 -t 300


echo "preparing DAE_DB_DIR_REMOTE: ${DAE_DB_DIR_REMOTE}"
mkdir -p ${DAE_DB_DIR_REMOTE}


docker run \
    --rm --network ${NETWORK} \
    --link ${CONTAINER_GPF_IMPALA}:impala \
    --entrypoint /bin/bash \
    --name ${CONTAINER_GPF_DEV} \
    --hostname ${CONTAINER_GPF_DEV} \
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
