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

# if [ -z $DAE_DB_DIR ];
# then
#     export DAE_DB_DIR="${WD}/data/data-hg19-startup"
# fi

if [ -z $BRANCH_NAME ];
then
    export BRANCH_NAME="master"
fi

if [ -z $BUILD_NUMBER ];
then
    export BUILD_NUMBER=0
fi

echo "JOB_NAME                      : ${JOB_NAME}"

if [ -z ${JOB_NAME} ];
then
    unset JENKINS
else
    export JENKINS="yes"
fi

echo "JENKINS                       : ${JENKINS}"
echo "WORKSPACE                    1: ${WORKSPACE}"
echo "WD                           1: ${WD}"


if [ ${BUILD_NUMBER} == "0" ];
then
    export DOWNLOADS=${WD}/downloads
else
    export DOWNLOADS=${WD}/downloads/builds
fi


export REGISTRY="registry.seqpipe.org:5000"
export IMAGE_GPF_BUILDER="seqpipe/seqpipe-anaconda-base:latest"
export GPF_VERSION=$(cat ${WD}/VERSION)


echo "GPF_VERSION                   : ${GPF_VERSION}"

export DAE_DB_DIR="${WD}/data/data-hg19-startup"
echo "DAE_DB_DIR                    : ${DAE_DB_DIR}"
export DAE_DB_DIR_REMOTE="${WD}/data/data-hg19-remote"
echo "DAE_DB_DIR_REMOTE             : ${DAE_DB_DIR_REMOTE}"

echo "BRANCH_NAME                   : ${BRANCH_NAME}"
echo "BUILD_NUMBER                  : ${BUILD_NUMBER}"

export GPF_SERIES=$(cut -d "." -f 1-2 <<<"${GPF_VERSION}")
echo "GPF_SERIES                    : ${GPF_SERIES}"

export GPF_TAG=${GPF_VERSION}_${BUILD_NUMBER}
echo "GPF_TAG                       : ${GPF_TAG}"


if [ -z $JENKINS ];
then
    export TAG="local"
else
    export TAG="${BRANCH_NAME}-${GPF_VERSION}-${BUILD_NUMBER}"
fi

export NETWORK="gpf-dev-network-${TAG}"
export NETWORK=$(tr '_' '-' <<<"${NETWORK}")
export NETWORK=$(tr '.' '-' <<<"${NETWORK}")

export CONTAINER_GPF_IMPALA="gpf-dev-impala-${TAG}"
export CONTAINER_GPF_IMPALA=$(tr '_' '-' <<<"${CONTAINER_GPF_IMPALA}")
export CONTAINER_GPF_IMPALA=$(tr '.' '-' <<<"${CONTAINER_GPF_IMPALA}")

export IMAGE_GPF_DEV="gpf-dev-image-${TAG}"
export IMAGE_GPF_DEV=$(tr '_' '-' <<<"${IMAGE_GPF_DEV}")
export IMAGE_GPF_DEV=$(tr '.' '-' <<<"${IMAGE_GPF_DEV}")
export IMAGE_GPF_DEV=${REGISTRY}/${IMAGE_GPF_DEV}:${GPF_TAG}

export CONTAINER_GPF_DEV="gpf-dev-${TAG}"
export CONTAINER_GPF_DEV=$(tr '_' '-' <<<"${CONTAINER_GPF_DEV}")
export CONTAINER_GPF_DEV=$(tr '.' '-' <<<"${CONTAINER_GPF_DEV}")

export CONTAINER_GPF_REMOTE="gpf-dev-remote-${TAG}"
export CONTAINER_GPF_REMOTE=$(tr '_' '-' <<<"${CONTAINER_GPF_REMOTE}")
export CONTAINER_GPF_REMOTE=$(tr '.' '-' <<<"${CONTAINER_GPF_REMOTE}")

export CONTAINER_TESTS="gpf-dev-tests-${TAG}"
export CONTAINER_TESTS=$(tr '_' '-' <<<"${CONTAINER_TESTS}")
export CONTAINER_TESTS=$(tr '.' '-' <<<"${CONTAINER_TESTS}")


echo "CONTAINER_GPF_IMPALA          : ${CONTAINER_GPF_IMPALA}"
echo "IMAGE_GPF_DEV                 : ${IMAGE_GPF_DEV}"
echo "CONTAINER_GPF_DEV             : ${CONTAINER_GPF_DEV}"
echo "CONTAINER_GPF_REMOTE          : ${CONTAINER_GPF_REMOTE}"
echo "CONTAINER_TESTS               : ${CONTAINER_TESTS}"
echo "NETWORK                       : ${NETWORK}"


. ${WD}/scripts/env.sh 



