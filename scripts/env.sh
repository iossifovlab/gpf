#!/bin/bash

set -e

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

if [ -z ${DOWNLOADS} ];
then
    export DOWNLOADS=${WD}/downloads
fi

export SCRIPTS=${WD}/scripts
echo "SCRIPTS                       : ${SCRIPTS}"

export RESULTS=${WD}/results
echo "RESULTS                       : ${RESULTS}"
mkdir -p ${RESULTS}

export IMPORT=${WD}/import
echo "IMPORT                        : ${IMPORT}"
mkdir -p ${IMPORT}
