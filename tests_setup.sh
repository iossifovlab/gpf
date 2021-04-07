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


# echo "removing GPF data..."
# docker run -d --rm \
#     -v ${WD}:/wd \
#     busybox:latest \
#     /bin/sh -c "rm -rf /wd/data/*"

# echo "removing downloaded data..."
# docker run -d --rm \
#     -v ${WD}:/wd \
#     busybox:latest \
#     /bin/sh -c "rm -rf /wd/downloads/*"

# echo "removing results..."
# docker run -d --rm \
#     -v ${WD}:/wd \
#     busybox:latest \
#     /bin/sh -c "rm -rf /wd/results/*"

mkdir -p ${WD}/downloads
mkdir -p ${WD}/results
mkdir -p ${WD}/data
mkdir -p ${WD}/import

cd ${WD}
docker build . -f ${WD}/Dockerfile -t ${IMAGE_GPF_DEV}

# ${SCRIPTS}/run_mysql.sh
${SCRIPTS}/download_gpf_data.sh
${SCRIPTS}/prepare_gpf_data.sh
${SCRIPTS}/prepare_gpf_remote.sh
${SCRIPTS}/run_gpf_remote.sh
${SCRIPTS}/run_gpf_dev.sh internal_run_test_data_import.sh


