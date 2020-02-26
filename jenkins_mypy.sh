#!/bin/bash

cd /code
mkdir mypy_report
mypy dae/dae wdae/wdae --pretty \
     --ignore-missing-imports \
     --warn-return-any \
     --warn-redundant-casts \
     --html-report mypy_report \
     || ( echo "Mypy failed to check typing, exited with $?"; exit 1 )
tar czf mypy_report.tar.gz mypy_report
