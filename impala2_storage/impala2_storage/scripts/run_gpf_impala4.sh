#!/bin/bash

set -e


export HAS_GPF_IMPALA=`docker ps -a | grep gpf_impala | sed -e "s/\s\{2,\}/\t/g" | cut -f 1`
export GPF_IMPALA_IMAGE='seqpipe/seqpipe-docker-impala:latest'

docker pull ${GPF_IMPALA_IMAGE}

if [[ -z $HAS_GPF_IMPALA ]]; then
    # create gpf_impala docker container

    docker create \
        --name gpf_impala \
        --hostname impala \
        -p 8020:8020 \
        -p 9870:9870 \
        -p 9864:9864 \
        -p 21050:21050 \
        ${GPF_IMPALA_IMAGE}
fi

export HAS_RUNNING_GPF_IMPALA=`docker ps | grep gpf_impala | sed -e "s/\s\{2,\}/\t/g" | cut -f 1`
echo "Has running impala: <${HAS_RUNNING_GPF_IMPALA}>"
if [[ -z $HAS_RUNNING_GPF_IMPALA ]]; then
    echo "starting gpf_impala container..."
    docker start gpf_impala
fi

echo "waiting gpf_impala container..."
docker exec gpf_impala /wait-for-it.sh -h localhost -p 21050 -t 300

echo ""
echo "==============================================="
echo "Local GPF Apache Impala container is READY..."
echo "==============================================="
echo ""


# echo ""
# echo "==============================================="
# echo "Installing custom GPF UDAFs.."
# echo "==============================================="
# echo ""

# docker exec gpf_impala /upload_udafs_to_hdfs.sh
# docker exec gpf_impala /create_udafs.sh

# echo ""
# echo "==============================================="
# echo "[DONE] Installing custom GPF UDAFs.."
# echo "==============================================="
# echo ""
