#!/usr/bin/env bash


cd userdocs/development/gpf/dae/dae/docs
make clean html
tar zcvf ../../../../../../gpf-html.tar.gz -C _build/ html/
cd -

cd userdocs
make clean html
tar zcvf ../gpf-user-html.tar.gz -C _build/ html/
cd -

