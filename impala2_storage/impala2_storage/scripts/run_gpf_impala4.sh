#!/bin/bash

set -e


export HAS_GPF_IMPALA4=`docker ps -a | grep gpf_impala4 | sed -e "s/\s\{2,\}/\t/g" | cut -f 1`
export GPF_IMPALA4_IMAGE='registry.seqpipe.org/seqpipe-impala4:latest'

docker pull ${GPF_IMPALA4_IMAGE}

if [[ -z $HAS_GPF_IMPALA4 ]]; then
    # create gpf_impala4 docker container

    docker create \
        --name gpf_impala4 \
        --hostname impala \
        -p 8020:8020 \
        -p 9870:9870 \
        -p 9864:9864 \
        -p 21050:21050 \
        ${GPF_IMPALA4_IMAGE}
fi

export HAS_RUNNING_GPF_IMPALA4=`docker ps | grep gpf_impala4 | sed -e "s/\s\{2,\}/\t/g" | cut -f 1`
echo "Has running impala: <${HAS_RUNNING_GPF_IMPALA4}>"
if [[ -z $HAS_RUNNING_GPF_IMPALA4 ]]; then
    echo "starting gpf_impala4 container..."
    docker start gpf_impala4
fi

echo "waiting gpf_impala4 container..."
docker exec gpf_impala4 /wait-for-it.sh -h localhost -p 21050 -t 300

echo ""
echo "==============================================="
echo "Local GPF Apache Impala container is READY..."
echo "==============================================="
echo ""
