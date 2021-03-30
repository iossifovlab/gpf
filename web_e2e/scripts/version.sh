#!/bin/bash

set -e

echo "WORKSPACE                    0: ${WORKSPACE}"
echo "WD                           0: ${WD}"

if [ -z ${WORKSPACE} ];
then
    export WORKSPACE=`pwd`
fi

if [ -z $WD ]; 
then
    export WD=$(pwd)
fi

if [ -z ${GPF_TAG} ]; 
then
    export GPF_TAG="latest"
fi

if [ -z $GS ]; 
then
    export GS="genotype_impala"
fi 

if [ -z $BUILD_NUMBER ];
then
    export BUILD_NUMBER=0
fi

echo "WORKSPACE                    1: ${WORKSPACE}"
echo "WD                           1: ${WD}"


export IMAGE_GPF_DEV="registry.seqpipe.org:5000/seqpipe-gpf-full:${GPF_TAG}"
export IMAGE_GPF_BUILDER="registry.seqpipe.org:5000/seqpipe-builder:${GPF_TAG}"

docker pull ${IMAGE_GPF_DEV}
docker pull ${IMAGE_GPF_BUILDER}

export GPF_VERSION=$(docker run --entrypoint /bin/cat ${IMAGE_GPF_DEV} /code/VERSION)
echo "IMAGE_GPF_DEV                 : ${IMAGE_GPF_DEV}"
echo "GPF_VERSION                   : ${GPF_VERSION}"
echo "BUILD_NUMBER                  : ${GPF_VERSION}"

export IMPORT=${WD}/import
echo "IMPORT                        : ${IMPORT}"
mkdir -p ${IMPORT}

export DAE_DB_DIR="${WD}/data/data-hg19-startup-${GS}"

echo "DAE_DB_DIR                    : ${DAE_DB_DIR}"

. ${WD}/scripts/env.sh 



