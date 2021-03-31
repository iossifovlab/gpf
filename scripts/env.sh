#!/bin/bash

set -e

echo "WORKSPACE                    2: ${WORKSPACE}"
echo "WD                           2: ${WD}"

if [ -z ${WORKSPACE} ];
then
    export WORKSPACE=`pwd`
fi

if [ -z $WD ]; then
    export WD=$(pwd)
fi

if [ -z $BUILD_NUMBER ];
then
    export BUILD_NUMBER=0
fi

echo "WORKSPACE                    3: ${WORKSPACE}"
echo "WD                           3: ${WD}"

if [ ${BUILD_NUMBER} == "0" ];
then
    export DOWNLOADS=${WD}/downloads
else
    export DOWNLOADS=${WD}/downloads/builds
fi

export SCRIPTS=${WD}/scripts
echo "SCRIPTS                       : ${SCRIPTS}"

export RESULTS=${WD}/results
echo "RESULTS                       : ${RESULTS}"
mkdir -p ${RESULTS}

export IMPORT=${WD}/import
echo "IMPORT                        : ${IMPORT}"
mkdir -p ${IMPORT}

echo "BRANCH_NAME                   : ${BRANCH_NAME}"
echo "BUILD_NUMBER                  : ${BUILD_NUMBER}"

export GPF_SERIES=$(cut -d "." -f 1-2 <<<"${GPF_VERSION}")
echo "GPF_SERIES                    : ${GPF_SERIES}"

export GPF_TAG=${GPF_VERSION}_${BUILD_NUMBER}
echo "GPF_TAG                       : ${GPF_TAG}"

export NETWORK="gpf-dev-network-${BRANCH_NAME}-${GPF_VERSION}-${BUILD_NUMBER}"
export NETWORK=$(tr '_' '-' <<<"${NETWORK}")
export NETWORK=$(tr '.' '-' <<<"${NETWORK}")

export CONTAINER_GPF_IMPALA="gpf-dev-impala-container-${BRANCH_NAME}-${GPF_VERSION}-${BUILD_NUMBER}"
export CONTAINER_GPF_IMPALA=$(tr '_' '-' <<<"${CONTAINER_GPF_IMPALA}")
export CONTAINER_GPF_IMPALA=$(tr '.' '-' <<<"${CONTAINER_GPF_IMPALA}")

export IMAGE_GPF_DEV="gpf-dev-image-${BRANCH_NAME}-${GPF_VERSION}-${BUILD_NUMBER}"
export IMAGE_GPF_DEV=$(tr '_' '-' <<<"${IMAGE_GPF_DEV}")
export IMAGE_GPF_DEV=$(tr '.' '-' <<<"${IMAGE_GPF_DEV}")
export IMAGE_GPF_DEV=${REGISTRY}/${IMAGE_GPF_DEV}:${GPF_TAG}

export CONTAINER_GPF_DEV="gpf-dev-${BRANCH_NAME}-${GPF_VERSION}-${BUILD_NUMBER}"
export CONTAINER_GPF_DEV=$(tr '_' '-' <<<"${CONTAINER_GPF_DEV}")
export CONTAINER_GPF_DEV=$(tr '.' '-' <<<"${CONTAINER_GPF_DEV}")

export CONTAINER_GPF_REMOTE="gpf-dev-remote-${BRANCH_NAME}-${GPF_VERSION}-${BUILD_NUMBER}"
export CONTAINER_GPF_REMOTE=$(tr '_' '-' <<<"${CONTAINER_GPF_REMOTE}")
export CONTAINER_GPF_REMOTE=$(tr '.' '-' <<<"${CONTAINER_GPF_REMOTE}")

export CONTAINER_TESTS="gpf-dev-tests-${BRANCH_NAME}-${GPF_VERSION}-${BUILD_NUMBER}"
export CONTAINER_TESTS=$(tr '_' '-' <<<"${CONTAINER_TESTS}")
export CONTAINER_TESTS=$(tr '.' '-' <<<"${CONTAINER_TESTS}")


echo "CONTAINER_GPF_IMPALA          : ${CONTAINER_GPF_IMPALA}"
echo "IMAGE_GPF_DEV                 : ${IMAGE_GPF_DEV}"
echo "CONTAINER_GPF_DEV             : ${CONTAINER_GPF_DEV}"
echo "CONTAINER_GPF_REMOTE          : ${CONTAINER_GPF_REMOTE}"
echo "CONTAINER_TESTS               : ${CONTAINER_TESTS}"
echo "NETWORK                       : ${NETWORK}"
