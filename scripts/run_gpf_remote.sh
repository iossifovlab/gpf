#!/bin/bash

# check this tutorial:
# https://pythonspeed.com/articles/activate-conda-dockerfile/
#

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

. ${WD}/scripts/utils.sh


run_gpf_impala


echo "using DAE_DB_DIR_REMOTE: ${DAE_DB_DIR_REMOTE}"
mkdir -p ${DAE_DB_DIR_REMOTE}

run_gpf_remote