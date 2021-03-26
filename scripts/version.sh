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

echo "WORKSPACE                    1: ${WORKSPACE}"
echo "WD                           1: ${WD}"

export REGISTRY="registry.seqpipe.org:5000"
export IMAGE_GPF_BUILDER="seqpipe/seqpipe-anaconda-base:latest"
export GPF_VERSION=$(cat ${WD}/VERSION)


echo "GPF_VERSION                   : ${GPF_VERSION}"

export DAE_DB_DIR="${WD}/data/data-hg19-startup"
echo "DAE_DB_DIR                    : ${DAE_DB_DIR}"
export DAE_DB_DIR_REMOTE="${WD}/data/data-hg19-remote"
echo "DAE_DB_DIR_REMOTE             : ${DAE_DB_DIR_REMOTE}"


if [ ${BUILD_NUMBER} == "0" ];
then
    export DOWNLOADS=${WD}/downloads
else
    export DOWNLOADS=${WD}/downloads/builds
fi
echo "DOWNLOADS                     : ${DOWNLOADS}"

. ${WD}/scripts/env.sh 



