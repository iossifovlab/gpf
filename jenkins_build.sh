#!/usr/bin/env bash

set -e

cd ${DAE_SOURCE_DIR}/dae && pip install -e . && cd -
cd ${DAE_SOURCE_DIR}/wdae && pip install -e . && cd -

cd ${DOCUMENTATION_DIR}/userdocs/development/gpf/dae/dae/docs
make clean html
tar zcvf ../../../../../../gpf-html.tar.gz -C _build/ html/
cd -

cd ${DOCUMENTATION_DIR}/userdocs
make clean html
tar zcvf ../gpf-user-html.tar.gz -C _build/ html/
cd -

