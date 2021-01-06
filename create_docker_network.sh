#!/bin/bash

export HAS_NETWORK=`docker network ls | grep ${GPF_DOCKER_NETWORK} | sed -e "s/\s\{2,\}/\t/g" | cut -f 1`
echo ${GPF_DOCKER_NETWORK}
if [[ -z $HAS_NETWORK ]]; then
    docker network create -d bridge ${GPF_DOCKER_NETWORK} || true
fi
