#!/bin/bash

if [[ -z $WD ]]; then
    SCRIPT_LOCATION=$(readlink -f "$0")
    SCRIPT_DIR=$(dirname "${SCRIPT_LOCATION}")
    export WD=$(dirname "${SCRIPT_DIR}")
fi

if [[ -z $GPF_REMOTE_DOCKER_CONTAINER ]]; then
    export GPF_REMOTE_DOCKER_CONTAINER="gpf_test_remote"
fi

if [[ -z $GPF_DOCKER_NETWORK ]]; then
    export GPF_DOCKER_NETWORK="gpf_base_local_1000"
fi

docker run --rm -it \
    --name ${GPF_REMOTE_DOCKER_CONTAINER} \
    --network ${GPF_DOCKER_NETWORK} \
    -v $WD/gpf_remote:/data \
    -v $WD:/code \
    -v $WD/iossifov_2014:/study \
    -p 21010:21010 \
    -e DAE_DB_DIR=/data \
    -e DAE_DATA_DIR=/data \
    -d \
    seqpipe/seqpipe-gpf-conda /code/scripts/run_remote_server.sh

docker exec ${GPF_REMOTE_DOCKER_CONTAINER} /code/scripts/wait-for-it.sh -h localhost -p 21010 -t 300

echo ""
echo "==========================================="
echo "======= Local GPF test remote ready ======="
echo "==========================================="
