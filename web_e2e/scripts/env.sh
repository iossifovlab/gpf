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

echo "WORKSPACE                    3: ${WORKSPACE}"
echo "WD                           3: ${WD}"


export DOWNLOADS=${WD}/downloads
echo "DOWNLOADS                     : ${DOWNLOADS}"

export SCRIPTS=${WD}/scripts
echo "SCRIPTS                       : ${SCRIPTS}"

export RESULTS=${WD}/results
echo "RESULTS                       : ${RESULTS}"
mkdir -p ${RESULTS}

if [ -z $E2E ]; then
    export E2E=${WD}
fi

echo "GPF_BRANCH                    : ${GPF_BRANCH}"
echo "BUILD_NUMBER                  : ${BUILD_NUMBER}"

export GPF_SERIES=$(cut -d "." -f 1-2 <<<"${GPF_VERSION}")
echo "GPF_SERIES                    : ${GPF_SERIES}"

export NETWORK="gpf-e2e-network-${GPF_TAG}-${GS}-${BUILD_NUMBER}"
export NETWORK=$(tr '_' '-' <<<"${NETWORK}")
export NETWORK=$(tr '.' '-' <<<"${NETWORK}")

export CONTAINER_GPF_IMPALA="gpf-e2e-impala-container-${GPF_TAG}-${GS}-${BUILD_NUMBER}"
export CONTAINER_GPF_IMPALA=$(tr '_' '-' <<<"${CONTAINER_GPF_IMPALA}")
export CONTAINER_GPF_IMPALA=$(tr '.' '-' <<<"${CONTAINER_GPF_IMPALA}")


export CONTAINER_GPF_DEV="gpf-e2e-dev-${GPF_TAG}-${GS}-${BUILD_NUMBER}"
export CONTAINER_GPF_DEV=$(tr '_' '-' <<<"${CONTAINER_GPF_DEV}")
export CONTAINER_GPF_DEV=$(tr '.' '-' <<<"${CONTAINER_GPF_DEV}")

export CONTAINER_MYSQL="gpf-e2e-mysql-${GPF_TAG}-${GS}-${BUILD_NUMBER}"
export CONTAINER_MYSQL=$(tr '_' '-' <<<"${CONTAINER_MYSQL}")
export CONTAINER_MYSQL=$(tr '.' '-' <<<"${CONTAINER_MYSQL}")


export CONTAINER_E2E_TESTS="gpf-e2e-tests-${GPF_TAG}-${GS}-${BUILD_NUMBER}"
export CONTAINER_E2E_TESTS=$(tr '_' '-' <<<"${CONTAINER_E2E_TESTS}")
export CONTAINER_E2E_TESTS=$(tr '.' '-' <<<"${CONTAINER_E2E_TESTS}")


echo "CONTAINER_GPF_IMPALA          : ${CONTAINER_GPF_IMPALA}"
echo "CONTAINER_GPF_DEV             : ${CONTAINER_GPF_DEV}"
echo "CONTAINER_E2E_TESTS           : ${CONTAINER_E2E_TESTS}"
echo "NETWORK                       : ${NETWORK}"
