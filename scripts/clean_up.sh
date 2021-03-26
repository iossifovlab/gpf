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

for container in ${CONTAINER_TESTS} ${CONTAINER_GPF_DEV} ${CONTAINER_GPF_REMOTE} ${CONTAINER_MYSQL} ${CONTAINER_GPF_IMPALA}; do

    export HAS_RUNNING_CONTAINER=`docker ps | grep ${container} | sed -e "s/\s\{2,\}/\t/g" | cut -f 1`
    if [ $HAS_RUNNING_CONTAINER ];
    then
        echo "stopping container ${container}"
        docker stop ${container}
    fi
    sleep 2


    export HAS_CONTAINER=`docker ps -a | grep ${container} | sed -e "s/\s\{2,\}/\t/g" | cut -f 1`
    if [ $HAS_CONTAINER ];
    then
        echo "removing container ${container}"
        docker rm ${container}
    fi
    sleep 2


done

export HAS_NETWORK=`docker network ls | grep ${NETWORK} | sed -e "s/\s\{2,\}/\t/g" | cut -f 1`
if [[ $HAS_NETWORK ]]; then
    echo "removing network ${container}"
    docker network rm ${NETWORK}
fi


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
