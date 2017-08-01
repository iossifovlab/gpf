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

```
date && pheno2DAE.py -p ssc.ped -i instruments/ -r guess -o ssc_5.db && date                                                                    
Tue Aug  1 14:22:19 EEST 2017
--------------------------------------------------------
CLASSIFICATION BOUNDARIES:
--------------------------------------------------------
{'classification': {'categorical': {'min_rank': 2},
                    'continuous': {'min_rank': 15},
                    'min_individuals': 20,
                    'ordinal': {'min_rank': 5}},
 'db': {'filename': 'ssc_5.db'},
 'family': {'composite_key': False},
 'instruments': 'instruments/',
 'pedigree': 'ssc.ped',
 'person': {'role': {'column': 'role', 'mapping': 'SPARK', 'type': 'guess'}},
 'skip': {'measures': []},
 'verbose': None}
--------------------------------------------------------
...
...

```



## Import of SPARK phenotype database

