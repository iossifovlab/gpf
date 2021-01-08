#!/usr/bin/bash


set -e

if [ -z $WORKSPACE ];
then
    export WORKSPACE=`pwd`
fi

if [ -z $DAE_DB_DIR ];
then
    export DAE_DB_DIR=${WORKSPACE}/data-hg19-startup
fi

if [ -z $DAE_GENOMIC_SCORES_HG19 ];
then
DAE_GENOMIC_SCORES_HG19="/data01/lubo/data/seq-pipeline/genomic-scores-hg19"
fi

if [ -z $DAE_GENOMIC_SCORES_HG38 ];
then
DAE_GENOMIC_SCORES_HG38="/data01/lubo/data/seq-pipeline/genomic-scores-hg38"
fi


echo "WORKSPACE=${WORKSPACE}"
SOURCE_DIR="${WORKSPACE}/userdocs/gpf"



docker run --rm \
    -v ${WORKSPACE}:/documentation \
    -v ${DAE_DB_DIR}:/data \
    -v ${SOURCE_DIR}:/documentation/userdocs/gpf \
    -v ${DAE_GENOMIC_SCORES_HG19}:/genomic-scores-hg19 \
    -v ${DAE_GENOMIC_SCORES_HG38}:/genomic-scores-hg38 \
    seqpipe/gpf-documetation:master \
    /documentation/scripts/jenkins_build.sh
