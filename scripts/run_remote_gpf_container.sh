#!/bin/bash

docker run --rm -it \
    --name gpf_test_remote \
    -v $PWD/gpf_remote:/data \
    -v $(dirname $PWD):/code \
    -p 21010:21010 \
    -e DAE_DB_DIR=/data \
    -e DAE_DATA_DIR=/data \
    -d \
    seqpipe-gpf-conda /code/scripts/run_remote_server.sh

docker exec gpf_test_remote /code/scripts/wait-for-it.sh -h localhost -p 21010 -t 300

echo ""
echo "==========================================="
echo "======= Local GPF test remote ready ======="
echo "==========================================="
