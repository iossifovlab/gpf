#!/usr/bin/env bash

set -e

rm -rf coverage/ && mkdir coverage

py.test -v \
    --doctest-plus --doctest-rst \
    --junitxml=coverage/doc-junit.xml \
    ${DOCUMENTATION_DIR}/userdocs/administration \
    ${DOCUMENTATION_DIR}/userdocs/development \
    ${DOCUMENTATION_DIR}/userdocs/user_interface \
    ${DOCUMENTATION_DIR}/userdocs/development/gpf/dae/dae/docs \
    ${DOCUMENTATION_DIR}/userdocs/development/gpf/wdae/wdae/docs

chmod a+rwx -R coverage

rm -rf \
	wdae-api.log wdae-debug.log \
	wdae_django_default.cache wdae_django_pre.cache

find . -name "*.pyc" -delete
