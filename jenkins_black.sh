#!/bin/bash

cd /code && black --line-length 79 --check . || { echo "Black failed to verify formatting, exited with $?"; exit 1 }
