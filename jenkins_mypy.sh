#!/bin/bash

cd /code

mypy dae/dae wdae/wdae --pretty --ignore-missing-imports --warn-return-any --warn-redundant-casts --html-report mypy_report
tar czf mypy_report.tar.gz mypy_report
rm -rf mypy_report
