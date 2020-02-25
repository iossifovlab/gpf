#!/bin/bash

cd /code && black --line-length 79 --check . || echo "black exited with $?"
