# Timing interesting queries

## Interesting queries


|query   | description                                | w1202s766e611 |
|--------|--------------------------------------------|---------------|
|q101    | get EVERYTHING in a gene                   |   5777        |
|q201    | get EVERYTHING in a family                 |   29375       |
|q301    | get INTERESTING in a family                |   919         |
|q401    | get all UR LGDs                            |   28311       |
|q501    | get UR LGDs in FRMP genes                  |   746         |
|q601    | get all UR LGDs in proband                 |   14441       |
|q701    | get interesting rare variants in quads     |   203150      |
|q801    | get interesting rare variants              |   1108452     |


## Study w1202s766e611

|query | count  | legacy   |  mysql  | mysql (2000 limit)|
|------|--------|----------|---------|-------------------|
|q101  | 5777   | 0.636s   | 0.143s  | 0.043s            |
|q201  | 29375  | 160.778s | 0.694s  | 0.045s            |
|q301  | 919    | 24.253s  | 0.297s  | 0.251s            |
|q401  | 28311  | 18.823s  | 2.371s  | 0.073s            |
|q501  | 746    | 18.271s  | 0.371s  | 0.351s            |
|q601  | 14441  | 20.210s  | 0.838s  | 0.108s            |
|q701  | 203150 | 55.503s  | 20.953s | 0.233s            |
|q801  | 1108452| 101.257s | 35.128s | 0.069s            |


## Study SSC_WG_510

|query | count   |  mysql  | mysql (2000 limit)|
|------|---------|---------|-------------------|
|q101  | 18884   | 1.783s  |                   |
|q201  | 5098637 | 2380s   | 0.203s            |
|q301  | 1607    | 3.475   |                   |
|q401  | 10228   | 1.040s  | 0.148s            |
|q501  | 456     | 0.0786s |                   |
|q601  | 5293    | 0.463s  |                   |
|q701  | 66348   | 1140s   | 46.9s             |
|q801  | 263243  | 24.3s   | 0.217s            |


## Study AGRE_WG_859

Import of `AGRE_WG_859` into MySQL
```
(daework) lubo@dory:~/Work/seq-pipeline/DATA-DEV-SIMONS-PRODUCTION/cccc/AGRE_WG_859$ date && \
    myisam_transmitted_import.py \
    -s AGRE_WG_859_sql_summary_variants_myisam.sql.gz \
    -f AGRE_WG_859_sql_family_variants_myisam.sql.gz \
    -e AGRE_WG_859_sql_gene_effect_variants_myisam.sql.gz \
    -H 127.0.0.1 -P 3311 -u root -p... -D agre_wg && \
    date
Fri Feb  9 11:38:25 EET 2018
...
Wed Feb 14 18:16:28 EET 2018
```
