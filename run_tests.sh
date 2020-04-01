#!/bin/bash

set -e


if [ -z $WD ]; then
    WD=$(realpath $(dirname $0))
fi

echo "WD=$WD"


if [[ -z $DOCKER_IMAGE ]]; then
    export DOCKER_IMAGE="iossifovlab/gpf_base_local:1000"
fi

if [[ -z $DOCKER_NETWORK ]]; then
    export DOCKER_NETWORK="gpf_base_local_1000"
fi

if [[ -z $DOCKER_CONTAINER_IMPALA ]]; then
    export DOCKER_CONTAINER_IMPALA="gpf_impala_local_1000"
fi


echo "----------------------------------------------"
echo "Starting impala gpf container..."
echo "----------------------------------------------"

echo "Looking for docker network ${DOCKER_NETWORK}"

export HAS_NETWORK=`docker network ls | grep ${DOCKER_NETWORK} | sed -e "s/\s\{2,\}/\t/g" | cut -f 1`
if [[ -z $HAS_NETWORK ]]; then
    docker network create -d bridge ${DOCKER_NETWORK} || true
fi

echo "Looking for docker container ${DOCKER_CONTAINER_IMPALA}"
export HAS_GPF_IMPALA=`docker ps -a | grep ${DOCKER_CONTAINER_IMPALA} | sed -e "s/\s\{2,\}/\t/g" | cut -f 1`

if [[ -z $HAS_GPF_IMPALA ]]; then
    # create gpf_impala docker container

    docker pull seqpipe/seqpipe-docker-impala:latest
    docker create \
    --name ${DOCKER_CONTAINER_IMPALA} \
    --hostname impala \
    --network ${DOCKER_NETWORK} \
    seqpipe/seqpipe-docker-impala:latest

fi

export HAS_RUNNING_GPF_IMPALA=`docker ps | grep ${DOCKER_CONTAINER_IMPALA} | sed -e "s/\s\{2,\}/\t/g" | cut -f 1`

echo "Has running impala: <${HAS_RUNNING_GPF_IMPALA}>"
if [[ -z $HAS_RUNNING_GPF_IMPALA ]]; then
    echo "starting gpf_impala container..."
    docker start ${DOCKER_CONTAINER_IMPALA}
fi

echo "----------------------------------------------"
echo "[DONE] Starting impala gpf container..."
echo "----------------------------------------------"

echo "----------------------------------------------"
echo "Build GPF docker image"
echo "----------------------------------------------"

docker build ${WD} -f ${WD}/Dockerfile -t ${DOCKER_IMAGE}

echo "----------------------------------------------"
echo "Waiting for impala..."
echo "----------------------------------------------"
docker run --rm \
    --network ${DOCKER_NETWORK} \
    --link ${DOCKER_CONTAINER_IMPALA}:impala \
    -v ${DAE_DB_DIR}:/data \
    -v ${WD}:/code \
    ${DOCKER_IMAGE} /code/scripts/wait-for-it.sh impala:21050 --timeout=240

echo "----------------------------------------------"
echo "[DONE] Waiting for impala..."
echo "----------------------------------------------"

echo "----------------------------------------------"
echo "Running tests..."
echo "----------------------------------------------"

docker run --rm \
    --network ${DOCKER_NETWORK} \
    --link ${DOCKER_CONTAINER_IMPALA}:impala \
    -v ${DAE_DB_DIR}:/data \
    -v ${WD}:/code \
    ${DOCKER_IMAGE} /code/scripts/docker_test.sh

echo "----------------------------------------------"
echo "[DONE] Running tests..."
echo "----------------------------------------------"

fi [[ $CLEANUP ]]; then

    echo "----------------------------------------------"
    echo "Cleaning up docker containers"
    echo "----------------------------------------------"
    docker stop ${DOCKER_CONTAINER_IMPALA}
    docker rm ${DOCKER_CONTAINER_IMPALA}
    docker network prune --force
    docker image rm ${DOCKER_IMAGE}
    echo "----------------------------------------------"
    echo "[DONE] Cleaning up docker containers"
    echo "----------------------------------------------"

fi