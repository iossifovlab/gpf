#!/bin/bash

set -e


if [ -z $1 ]; then
    export GS="genotype_impala"
else
    export GS="${1}"
fi 

if [ -z ${WORKSPACE} ];
then
    export WORKSPACE=`pwd`
fi

if [ -z ${WD} ];
then
    export WD=${WORKSPACE}
fi


. ${WD}/scripts/version.sh


echo "GS                            : ${GS}"
echo "IMAGE_GPF_DEV                 : ${IMAGE_GPF_DEV}"


export HAS_NETWORK=`docker network ls | grep ${NETWORK} | sed -e "s/\s\{2,\}/\t/g" | cut -f 1`
if [[ -z $HAS_NETWORK ]]; then
    echo "going to create docker network ${NETWORK}"
    docker network create ${NETWORK}
fi


export HAS_GPF_MYSQL=`docker ps | grep ${CONTAINER_MYSQL} | sed -e "s/\s\{2,\}/\t/g" | cut -f 1`
if [[ -z $HAS_GPF_MYSQL ]]; then
    echo "going to start mysql docker container ${CONTAINER_MYSQL}"

    docker pull mysql:5.7

    docker run --rm -d \
        --name ${CONTAINER_MYSQL} \
        --network ${NETWORK} \
        -e "MYSQL_DATABASE=gpf" \
        -e "MYSQL_USER=seqpipe" \
        -e "MYSQL_PASSWORD=secret" \
        -e "MYSQL_ROOT_PASSWORD=secret" \
        -e "MYSQL_PORT=3306" \
        mysql:5.7 \
        --character-set-server=utf8 --collation-server=utf8_bin

fi

echo "waiting ${CONTAINER_MYSQL} container..."


docker run --rm \
    --network ${NETWORK} \
    --link ${CONTAINER_MYSQL}:${CONTAINER_MYSQL} \
    --entrypoint /bin/bash \
    ${IMAGE_GPF_DEV} \
    -c "/code/scripts/wait-for-it.sh ${CONTAINER_MYSQL}:3306 --timeout=360"

sleep 5

echo ""
echo "==============================================="
echo "GPF MySQL is READY..."
echo "==============================================="
echo ""
