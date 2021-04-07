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


cd ${WD}

${SCRIPTS}/clean_up_docker.sh
${SCRIPTS}/clean_up_directories.sh
