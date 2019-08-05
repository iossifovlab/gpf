#!/bin/bash

export T=$DAE_SOURCE_DIR/tests/data_import_test
export D=$DAE_DB_DIR/testSt-tmp/
rm -rf $D
mkdir -p $D

ped2NucFam.py $T/fam.ped $D/nuc-fam.ped

# to preserve the pheno columns
cp $T/nuc-fam.ped $D/nuc-fam-phn.ped

dnv2DAE.py $D/nuc-fam.ped $T/denovo.csv -m , -i SP_id -c CHROM -p POS -r REF -a ALT -o $D/dnvNuc
pheno2dae.py -f $D/nuc-fam-phn.ped -i $T/instruments/ -o $D/test.db

vcf2DAE.py $D/nuc-fam.ped $T/calls.vcf.gz -o $D/tmNuc
vcf2DAE.py $D/nuc-fam.ped $T/fam1.vcf,$T/fam2.vcf,$T/fam3.vcf -o $D/tmSmallNucFam 
vcf2DAE.py $T/fam.ped $T/fam1.vcf,$T/fam2.vcf,$T/fam3.vcf -o $D/tmSmallFam
