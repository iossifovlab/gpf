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


docker run \
    -it --rm \
    --entrypoint /bin/bash \
    -v ${WD}:/code \
    -v ${SCRIPTS}:/scripts \
    -e GPF_TAG=${GPF_TAG} \
    -e WORKSPACE="/" \
    -e WD="/" \
    ${IMAGE_GPF_DEV} -c "/opt/conda/bin/conda run --no-capture-output -n gpf /scripts/internal_run_mypy.sh"
