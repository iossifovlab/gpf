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

## Regenerate pheno browser cache

To regenerate pheno browser cache you need to use `manage.py` *Django* mangement
script using the special command `pheno_browser_cache`.

This command supports help option:

```
cd wdae
./manage.py pheno_browser_cache -h
usage: manage.py pheno_browser_cache [-h] [--version] [-v {0,1,2,3}]
                                     [--settings SETTINGS]
                                     [--pythonpath PYTHONPATH] [--traceback]
                                     [--no-color] [-f] [-p PHENO]

Rebuild pheno browser static figures cache

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
...
  -f, --force           Force recalculation of static resources
  -p PHENO, --pheno PHENO
                        Specify with pheno db to use. By default works on all
                        configured pheno DBs
```

Part of the output of this command, that is common for all *Django* commands is
skipped.

By default this command tries to rebuild the pheno browser figures cache for
all configured phenotype DBs. If you want to rebuild the cache for only one 
specific phenotype DB you can specify it by using `-p` (`--pheno`) option:

```
./manage.py pheno_browser_cache -p testSt
going to recaclulate ['testSt']
checking pheno browser cache for testSt
        cache OK
```

By default `pheno_browser_cache` command performs a check if pheno DB has 
changed and if the pheno browser figures cache needs to be rebuild. If the pheno
DB has changed the cache rebuild is trigured, otherwise the cache rebuild is
skipped.

If you need to force rebuild of pheno browser cache you can user `-f` (`--force`)
optioin:

```
./manage.py pheno_browser_cache -p testSt -f
going to recaclulate ['testSt']
checking pheno browser cache for testSt
        cache RECOMPUTING
testSt
...
...
```
