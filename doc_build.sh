#!/usr/bin/env bash


cd gpf/DAE/docs
rm -rf _build/ 
make html
tar zcvf ../../../gpf-html.tar.gz -C _build/ html/
cd -

cd userdocs
rm -rf _build/
make html
tar zcvf ../gpf-user-html.tar.gz -C _build/ html/
cd -

