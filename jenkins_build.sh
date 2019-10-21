#!/usr/bin/env bash

cd ${DOCUMENTATION_DIR}/userdocs/gpf/dae/dae/docs
make clean html
tar zcvf ../../../../../../gpf-html.tar.gz -C _build/ html/
cd -

cd ${DOCUMENTATION_DIR}/userdocs
make clean html
tar zcvf ../gpf-user-html.tar.gz -C _build/ html/
cd -

