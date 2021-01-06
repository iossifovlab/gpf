#!/bin/bash

if [[ -z $WD ]]; then
    SCRIPT_LOCATION=$(readlink -f "$0")
    SCRIPT_DIR=$(dirname "${SCRIPT_LOCATION}")
    export WD=$(dirname "${SCRIPT_DIR}")
fi

if [[ -z $GPF_REMOTE_DOCKER_CONTAINER ]]; then
    export GPF_REMOTE_DOCKER_CONTAINER="gpf_test_remote"
fi

if [[ -z $GPF_TEST_REMOTE_HOSTNAME ]]; then
    export GPF_TEST_REMOTE_HOSTNAME="gpfremote"
fi

if [[ -z $GPF_DOCKER_NETWORK ]]; then
    docker run --rm -it \
        --name ${GPF_REMOTE_DOCKER_CONTAINER} \
        -v $WD/gpf_remote:/data \
        -v $WD:/code \
        -v $WD/iossifov_2014:/study \
        -p 21010:21010 \
        -e DAE_DB_DIR=/data \
        -e DAE_DATA_DIR=/data \
        -e TEST_REMOTE_HOST=${GPF_TEST_REMOTE_HOSTNAME} \
        -d \
        seqpipe/seqpipe-gpf-conda /code/scripts/run_remote_server.sh
else
    export HAS_NETWORK=`docker network ls | grep ${GPF_DOCKER_NETWORK} | sed -e "s/\s\{2,\}/\t/g" | cut -f 1`
    echo ${GPF_DOCKER_NETWORK}
    if [[ -z $HAS_NETWORK ]]; then
        docker network create -d bridge ${GPF_DOCKER_NETWORK} || true
    fi

    docker run --rm -it \
        --name ${GPF_REMOTE_DOCKER_CONTAINER} \
        --hostname $GPF_TEST_REMOTE_HOSTNAME \
        --network ${GPF_DOCKER_NETWORK} \
        -v $WD/gpf_remote:/data \
        -v $WD:/code \
        -v $WD/iossifov_2014:/study \
        -e DAE_DB_DIR=/data \
        -e DAE_DATA_DIR=/data \
        -e TEST_REMOTE_HOST=${GPF_TEST_REMOTE_HOSTNAME} \
        -d \
        seqpipe/seqpipe-gpf-conda /code/scripts/run_remote_server.sh
fi

docker exec ${GPF_REMOTE_DOCKER_CONTAINER} /code/scripts/wait-for-it.sh -h localhost -p 21010 -t 300
# $WD/scripts/wait-for-it.sh -h localhost -p 21010 -t 300

echo ""
echo "==========================================="
echo "======= Local GPF test remote ready ======="
echo "==========================================="
