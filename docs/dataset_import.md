# Dataset import and configuration

## Break down pedigree file to nuclear families

```
ped2NucFam.py $T/fam.ped nuc-fam.ped
```

## Import denovo variants

```
dnv2DAE.py nuc-fam.ped $T/denovo.csv \
    -m , -i SP_id -c CHROM -p POS -r REF -a ALT \
    -o dnvNuc
```


## Import phenotype data


```
pheno2DAE.py -f nuc-fam.ped -i $T/instruments/ -o test.db
```

## Import VCF variants data

```
vcf2DAE.py nuc-fam.ped $T/calls.vcf.gz -o tmNuc
vcf2DAE.py nuc-fam.ped $T/fam1.vcf,$T/fam2.vcf,$T/fam3.vcf -o tmSmallNucFam 
vcf2DAE.py $T/fam.ped $T/fam1.vcf,$T/fam2.vcf,$T/fam3.vcf -o tmSmallFam
```
