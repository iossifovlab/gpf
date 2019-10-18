#!/usr/bin/env bash

cd ${DOCUMENTATION_DIR}/userdocs/development/gpf/dae/dae/docs
make clean html doctest
tar zcvf ../../../../../../gpf-html.tar.gz -C _build/ html/
cd -

cd ${DOCUMENTATION_DIR}/userdocs
make clean html doctest
tar zcvf ../gpf-user-html.tar.gz -C _build/ html/
cd -

