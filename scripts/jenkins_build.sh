#!/usr/bin/env bash

pip install sphinx_autorun

cd /documentation/userdocs/gpf/dae && pip install -e . && cd -
cd /documentation/userdocs/gpf/wdae && pip install -e . && cd -
cd /documentation/userdocs/gpf/dae_conftests && pip install -e . && cd -

cd /documentation/userdocs/gpf/dae/dae/docs
make clean html
tar zcvf ../../../../../gpf-html.tar.gz -C _build/ html/
cd -

cd /documentation/userdocs/gpf/wdae/wdae/docs
make clean html
tar zcvf ../../../../../gpf-wdae-html.tar.gz -C _build/ html/
cd -

cd /documentation/userdocs
make clean html
tar zcvf ../gpf-user-html.tar.gz -C _build/ html/
cd -

rm -rf \
	wdae-api.log wdae-debug.log \
	wdae_django_default.cache wdae_django_pre.cache

find . -name "*.pyc" -delete
