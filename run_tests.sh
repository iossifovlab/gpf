#!/bin/bash

set -e


if [ -z $WD ]; then
    WD=$(realpath $(dirname $0))
fi

echo "WD=$WD"


if [[ -z $GPF_DOCKER_IMAGE ]]; then
    export GPF_DOCKER_IMAGE="iossifovlab/gpf_base_local:1000"
fi

if [[ -z $GPF_DOCKER_NETWORK ]]; then
    export GPF_DOCKER_NETWORK="gpf_base_local_1000"
fi

if [[ -z $GPF_IMPALA_DOCKER_CONTAINER ]]; then
    export GPF_IMPALA_DOCKER_CONTAINER="gpf_impala_local_1000"
fi

if [[ -z $GPF_REMOTE_DOCKER_CONTAINER ]]; then
    export GPF_REMOTE_DOCKER_CONTAINER="gpf_test_remote"
fi

if [[ -z $GPF_TEST_REMOTE_HOSTNAME ]]; then
    export GPF_TEST_REMOTE_HOSTNAME="gpf_test_remote"
fi

echo "----------------------------------------------"
echo "Starting impala gpf container..."
echo "----------------------------------------------"

echo "Looking for docker network ${GPF_DOCKER_NETWORK}"

export HAS_NETWORK=`docker network ls | grep ${GPF_DOCKER_NETWORK} | sed -e "s/\s\{2,\}/\t/g" | cut -f 1`
if [[ -z $HAS_NETWORK ]]; then
    docker network create -d bridge ${GPF_DOCKER_NETWORK} || true
fi

echo "Looking for docker container ${GPF_IMPALA_DOCKER_CONTAINER}"
export HAS_GPF_IMPALA=`docker ps -a | grep ${GPF_IMPALA_DOCKER_CONTAINER} | sed -e "s/\s\{2,\}/\t/g" | cut -f 1`

if [[ -z $HAS_GPF_IMPALA ]]; then
    # create gpf_impala docker container

    docker pull seqpipe/seqpipe-docker-impala:latest
    docker create \
    --name ${GPF_IMPALA_DOCKER_CONTAINER} \
    --hostname impala \
    --network ${GPF_DOCKER_NETWORK} \
    seqpipe/seqpipe-docker-impala:latest

fi

export HAS_RUNNING_GPF_IMPALA=`docker ps | grep ${GPF_IMPALA_DOCKER_CONTAINER} | sed -e "s/\s\{2,\}/\t/g" | cut -f 1`

echo "Has running impala: <${HAS_RUNNING_GPF_IMPALA}>"
if [[ -z $HAS_RUNNING_GPF_IMPALA ]]; then
    echo "starting gpf_impala container..."
    docker start ${GPF_IMPALA_DOCKER_CONTAINER}
fi

echo "----------------------------------------------"
echo "[DONE] Starting impala gpf container..."
echo "----------------------------------------------"

echo "----------------------------------------------"
echo "Build GPF docker image"
echo "----------------------------------------------"

docker build ${WD} -f ${WD}/Dockerfile -t ${GPF_DOCKER_IMAGE}

echo "----------------------------------------------"
echo "Waiting for impala..."
echo "----------------------------------------------"
docker run --rm \
    --network ${GPF_DOCKER_NETWORK} \
    --link ${GPF_IMPALA_DOCKER_CONTAINER}:impala \
    -v ${DAE_DB_DIR}:/data \
    -v ${WD}:/code \
    ${GPF_DOCKER_IMAGE} /code/scripts/wait-for-it.sh impala:21050 --timeout=240

echo "----------------------------------------------"
echo "[DONE] Waiting for impala..."
echo "----------------------------------------------"

echo "----------------------------------------------"
echo "Running tests..."
echo "----------------------------------------------"

docker run --rm \
    --network ${GPF_DOCKER_NETWORK} \
    --link ${GPF_IMPALA_DOCKER_CONTAINER}:impala \
    --link ${GPF_REMOTE_DOCKER_CONTAINER}:${GPF_TEST_REMOTE_HOSTNAME} \
    -v ${DAE_DB_DIR}:/data \
    -v ${WD}:/code \
    -e TEST_REMOTE_HOST=${GPF_TEST_REMOTE_HOSTNAME} \
    ${GPF_DOCKER_IMAGE} /code/scripts/docker_test.sh

echo "----------------------------------------------"
echo "[DONE] Running tests..."
echo "----------------------------------------------"

if [[ $CLEANUP ]]; then

    echo "----------------------------------------------"
    echo "Cleaning up remote container..."
    echo "----------------------------------------------"
    docker stop ${GPF_REMOTE_DOCKER_CONTAINER}
    docker rm ${GPF_REMOTE_DOCKER_CONTAINER}
    echo "----------------------------------------------"
    echo "[DONE] Cleaning up remote container"
    echo "----------------------------------------------"

    echo "----------------------------------------------"
    echo "Cleaning up impala docker containers"
    echo "----------------------------------------------"
    docker stop ${GPF_IMPALA_DOCKER_CONTAINER}
    docker rm ${GPF_IMPALA_DOCKER_CONTAINER}
    echo "----------------------------------------------"
    echo "[DONE] Cleaning up impala docker containers"
    echo "----------------------------------------------"

    echo "----------------------------------------------"
    echo "Cleaning up docker"
    echo "----------------------------------------------"
    docker network prune --force
    docker image rm ${GPF_DOCKER_IMAGE}
    echo "----------------------------------------------"
    echo "[DONE] Cleaning up docker"
    echo "----------------------------------------------"

fi
