#!/usr/bin/env bash

set -e

rm -rf coverage/ && mkdir coverage

py.test -v \
    --doctest-plus --doctest-rst \
    --junitxml=coverage/doc-junit.xml \
    userdocs/administration \
    userdocs/development \
    userdocs/user_interface \
    ${DOCKER_SOURCE_DIR}/dae/dae/docs \
    ${DOCKER_SOURCE_DIR}/wdae/wdae/docs

chmod a+rwx -R coverage

rm -rf \
	wdae-api.log wdae-debug.log \
	wdae_django_default.cache wdae_django_pre.cache

find . -name "*.pyc" -delete
