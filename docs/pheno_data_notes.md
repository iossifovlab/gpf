# Phenotype Data Tools

## Import of SSC phenotype database v15

* The pedigree file for SSC was prepared with `notebooks/ssc_helpers.py`. The
result is stored into `data-dev/pheno/15/ssc.ped`.

* All instruments are put into directory `data-dev/pheno/15/instruments`. The
directory structure is as follows:

```
15
└── instruments
    ├── Designated Unaffected Sibling Data
    ├── Father Data
    ├── Mother Data
    ├── MZ Twin Data
    ├── Other Sibling Data
    └── Proband Data
```

* To import phenotype data we used `pheno2DAE` tool with following command:
```
pheno2DAE.py -p ssc.ped -i instruments/ -r guess -o ssc_15.db
```

## Import of SPARK phenotype database

