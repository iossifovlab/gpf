#!/bin/bash

set -e


if [ -z ${WORKSPACE} ];
then
    export WORKSPACE=`pwd`
fi

if [ -z $WD ]; then
    export WD=$(pwd)
fi

if [ -z ${BUILD_NUMBER} ];
then
    export BUILD_NUMBER=0
fi

mkdir -p builds
rm -rf builds/*
GPF_VERSION=$(cat ${WORKSPACE}/VERSION)

cd ${WORKSPACE}

tar zcvf builds/gpf-${BRANCH_NAME}-${GPF_VERSION}.${BUILD_NUMBER}.tar.gz \
    --exclude builds \
    --exclude .git \
    --exclude gpf_remote \
    --exclude *.vscode* \
    --exclude *comp-data* \
    --exclude *__pycache__* \
    --exclude *.pytest_cache* \
    --exclude *.snakemake* \
    --exclude *.mypy_cache* \
    --exclude genotype-*.tar.gz \
    --exclude *.bak*\
    --exclude test_results \
    --exclude data-hg19*.tar.gz \
    --exclude data-hg19-startup \
    --exclude dae_conftests \
    --transform "s/^\./gpf/" \
    .

cp conda-environment.yml \
    builds/conda-environment-${BRANCH_NAME}-${GPF_VERSION}.${BUILD_NUMBER}.yml

