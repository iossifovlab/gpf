#!/bin/bash

set -e

if [ -z ${WORKSPACE} ];
then
    export WORKSPACE=`pwd`
fi

if [ -z ${WD} ];
then
    export WD=${WORKSPACE}
fi

. ${WD}/scripts/version.sh


echo "removing GPF data..."
docker run -d --rm \
    -v ${WD}:/wd \
    busybox:latest \
    /bin/sh -c "rm -rf /wd/data/*"

echo "removing GPF import..."
docker run -d --rm \
    -v ${WD}:/wd \
    busybox:latest \
    /bin/sh -c "rm -rf /wd/import/*"

echo "removing downloaded data..."
docker run -d --rm \
    -v ${WD}:/wd \
    busybox:latest \
    /bin/sh -c "rm -rf /wd/downloads/*"

# echo "removing results..."
# docker run -d --rm \
#     -v ${WD}:/wd \
#     busybox:latest \
#     /bin/sh -c "rm -rf /wd/results/*"
