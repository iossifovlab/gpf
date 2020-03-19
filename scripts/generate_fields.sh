#!/usr/bin/env bash

for file in ../userdocs/administration/gpf_tools/*.rst
do
    python ./generate_fields.py $file
done;
