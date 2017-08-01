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
Tue Aug  1 15:34:13 EEST 2017
```



## Import of VIP phenotype database

```
date && pheno2DAE.py -p nuc_svip.ped -i SVIP_16p11.2/ -r guess -o vip_3.db && date                                                             
Tue Aug  1 15:51:35 EEST 2017
--------------------------------------------------------
CLASSIFICATION BOUNDARIES:
--------------------------------------------------------
{'classification': {'categorical': {'min_rank': 2},
                    'continuous': {'min_rank': 15},
                    'min_individuals': 20,
                    'ordinal': {'min_rank': 5}},
 'db': {'filename': 'vip_3.db'},
 'family': {'composite_key': False},
 'instruments': 'SVIP_16p11.2/',
 'pedigree': 'nuc_svip.ped',
 'person': {'role': {'column': 'role', 'mapping': 'SPARK', 'type': 'guess'}},
 'skip': {'measures': []},
 'verbose': None}
--------------------------------------------------------
('SVIP_16p11.2/', 'wasi.csv')
('SVIP_16p11.2/', 'mhi_adult.csv')
('SVIP_16p11.2/', 'previous_diagnosis.csv')
...
...
('vineland_ii', 'written_v_score', <Box: {'measure_id': 'vineland_ii.written_v_score', 'individuals': 110, 'instrument_name': 'vineland_ii', 'measure_name': 'written_v_score', 'measure_type': <MeasureType.continuous: 1>, 'default_filter': None}>)
Tue Aug  1 16:01:41 EEST 2017
```
