#!/bin/bash

cd /code

if mypy dae/dae wdae/wdae --pretty --ignore-missing-imports --warn-return-any --warn-redundant-casts --html-report mypy_report
then
	tar czf mypy_report.tar.gz mypy_report
else
	echo "Mypy failed to check typing, exited with $?"; exit 1
fi
