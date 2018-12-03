#!/bin/sh

# echo $1

head -n 1 $1
for f in $@; do
  # echo $f
  tail -n +2 $f
done
