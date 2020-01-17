#!/usr/bin/env bash

set -e

cd ${DOCUMENTATION_DIR}/userdocs/gpf/dae && pip install -e . && cd -
cd ${DOCUMENTATION_DIR}/userdocs/gpf/wdae && pip install -e . && cd -
cd ${DOCUMENTATION_DIR}/userdocs/gpf/dae_conftests && pip install -e . && cd -

rm -rf coverage/ && mkdir coverage

py.test -v \
    --doctest-modules --doctest-plus \
    --doctest-rst --text-file-format rst \
    --junitxml=coverage/doc-junit.xml \
    ${DOCUMENTATION_DIR}/userdocs/administration \
    ${DOCUMENTATION_DIR}/userdocs/development \
    ${DOCUMENTATION_DIR}/userdocs/user_interface \
    ${DOCUMENTATION_DIR}/userdocs/gpf/dae/dae/docs \
    ${DOCUMENTATION_DIR}/userdocs/gpf/wdae/wdae/docs

chmod a+rwx -R coverage

rm -rf \
	wdae-api.log wdae-debug.log \
	wdae_django_default.cache wdae_django_pre.cache

find . -name "*.pyc" -delete
