#!/bin/bash
# Script intended for running mysql container with seqpipe user and gpf database

set -e


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


run_mysql