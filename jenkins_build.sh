#!/usr/bin/env bash

set -e

cd dae && pip install -e . && cd -
cd wdae && pip install -e . && cd -

cd /documentation/userdocs/development/gpf/dae/dae/docs
make clean html
tar zcvf ../../../../../../gpf-html.tar.gz -C _build/ html/
cd -

cd /documentation/userdocs
make clean html
tar zcvf ../gpf-user-html.tar.gz -C _build/ html/
cd -

