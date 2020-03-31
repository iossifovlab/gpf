#!/bin/bash

set -e

export HAS_NETWORK=`docker network ls | grep ${DOCKER_NETWORK} | sed -e "s/\s\{2,\}/\t/g" | cut -f 1`
if [[ -z $HAS_NETWORK ]]; then
    docker network create -d bridge ${DOCKER_NETWORK} || true
fi

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

# docker run -d \
#     --name ${DOCKER_CONTAINER_IMPALA} \
#     --hostname impala \
#     --network ${DOCKER_NETWORK} \
#     --cidfile ${DOCKER_CONTAINER_IMPALA}.id \
#     seqpipe/seqpipe-docker-impala:latest
