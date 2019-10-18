#!/usr/bin/env bash

set -e

cd ${DAE_SOURCE_DIR}/dae && pip install -e . && cd -
cd ${DAE_SOURCE_DIR}/wdae && pip install -e . && cd -
