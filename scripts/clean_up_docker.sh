#!/bin/bash

set -e


export HAS_GPF_IMPALA=`docker ps -a | grep ${GPF_IMPALA_DOCKER_CONTAINER} | sed -e "s/\s\{2,\}/\t/g" | cut -f 1`
export HAS_GPF_REMOTE=`docker ps -a | grep ${GPF_REMOTE_DOCKER_CONTAINER} | sed -e "s/\s\{2,\}/\t/g" | cut -f 1`


echo "----------------------------------------------"
echo "Cleaning up remote container..."
echo "----------------------------------------------"

if [[ ! -z $HAS_GPF_REMOTE ]]; then
    docker stop ${GPF_REMOTE_DOCKER_CONTAINER}
fi
echo "----------------------------------------------"
echo "[DONE] Cleaning up remote container"
echo "----------------------------------------------"



echo "----------------------------------------------"
echo "Cleaning up impala docker containers"
echo "----------------------------------------------"
if [[ ! -z $HAS_GPF_IMPALA ]]; then
    docker stop ${GPF_IMPALA_DOCKER_CONTAINER}
    docker rm ${GPF_IMPALA_DOCKER_CONTAINER}
fi

echo "----------------------------------------------"
echo "[DONE] Cleaning up impala docker containers"
echo "----------------------------------------------"

echo "----------------------------------------------"
echo "Cleaning up docker"
echo "----------------------------------------------"
docker image rm ${GPF_DOCKER_IMAGE}
docker network prune --force
echo "----------------------------------------------"
echo "[DONE] Cleaning up docker"
echo "----------------------------------------------"

