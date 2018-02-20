#!/bin/bash

pref=$1
echo "chr	pos	refA	altA	effectType	effectGene	effectDetails" > $pref-eff.txt
cat $pref.vcf| grep -v ^# | cut -f 1,2,4,5 | annotate_variants.py - -H -c 1 -p 2 -r 3 -a 4 | grep -v ^# >> $pref-eff.txt
