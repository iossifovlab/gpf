#!/bin/bash

set -e

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


echo "removing GPF data..."
docker run -d --rm \
    -v ${WD}:/wd \
    busybox:latest \
    /bin/sh -c "rm -rf /wd/data"

echo "removing downloaded data..."
docker run -d --rm \
    -v ${WD}:/wd \
    busybox:latest \
    /bin/sh -c "rm -rf /wd/downloads"

echo "removing results..."
docker run -d --rm \
    -v ${WD}:/wd \
    busybox:latest \
    /bin/sh -c "rm -rf /wd/results"

mkdir -p ${WD}/downloads
mkdir -p ${WD}/results
mkdir -p ${WD}/data


${SCRIPTS}/run_mysql.sh
${SCRIPTS}/download_gpf_data.sh
${SCRIPTS}/prepare_gpf_data.sh
${SCRIPTS}/run_gpf.sh


