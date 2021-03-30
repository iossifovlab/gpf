#!/bin/bash

set -e

# if [ -z ${BUILD_NUMBER} ];
# then

#     echo "Local build... Exposing GPF docker container on port 8080"
#     export EXPOSE_PORT="-p 8080:80"
# else
#     export EXPOSE_PORT=""
# fi


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
    docker network create ${NETWORK}
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



echo ""
echo "==============================================="
echo "GPF starting..."
echo "==============================================="
echo ""

docker run --rm -d \
    --name ${CONTAINER_GPF_DEV} \
    --network ${NETWORK} \
    --link ${CONTAINER_MYSQL}:${CONTAINER_MYSQL} \
    --link ${CONTAINER_GPF_IMPALA}:impala \
    -v "${DAE_DB_DIR}:/data" \
    -e DAE_DB_DIR=/data \
    -e WDAE_DB_NAME="gpf" \
    -e WDAE_DB_USER="seqpipe" \
    -e WDAE_DB_PASSWORD="secret" \
    -e WDAE_DB_HOST="${CONTAINER_MYSQL}" \
    -e WDAE_DB_PORT="3306" \
    -e WDAE_SECRET_KEY="123456789012345678901234567890123456789012345678901234567890" \
    -e WDAE_ALLOWED_HOST="*" \
    -e WDAE_DEBUG="True" \
    -e WDAE_PUBLIC_HOSTNAME="locahost" \
    -e GPF_PREFIX="gpf" \
    -e WDAE_PREFIX="gpf" \
    -e IMPALA_HOSTS="${CONTAINER_GPF_IMPALA}" \
    ${IMAGE_GPF_DEV}

echo ""
echo "==============================================="
echo "GPF waiting for gunicorn on 9001..."
echo "==============================================="
echo ""

docker exec \
    ${CONTAINER_GPF_DEV} \
    /code/scripts/wait-for-it.sh localhost:9001 --timeout=360

echo ""
echo "==============================================="
echo "GPF waiting for apache on 80..."
echo "==============================================="
echo ""

docker exec \
    ${CONTAINER_GPF_DEV} \
    /code/scripts/wait-for-it.sh localhost:80 --timeout=360

echo ""
echo "==============================================="
echo "GPF started..."
echo "==============================================="
echo ""

docker exec \
    ${CONTAINER_GPF_DEV} \
    /code/wdae/wdae/wdae_create_dev_users.sh



echo ""
echo "==============================================="
echo "GPF test users created..."
echo "==============================================="
echo ""
