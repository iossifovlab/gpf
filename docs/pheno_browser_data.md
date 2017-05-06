# Pheno Tool and Pheno Browser Data Configuration

## Configuration

Pheno Browser configuration could be found into `data-dev` directory, file named
`phenoDB.conf`.

Let say we have the following `phenoDB.conf`

```
[pheno]
dbs=ssc,vip
browser_dir = %(wd)s/pheno/browser

[ssc]
cache_file = ssc_v15.db
age = pheno_common:age
nonverbal_iq = pheno_common:non_verbal_iq

[vip]
cache_file = vip_1.db
age = measure.eval_age_months
nonverbal_iq = diagnosis_summary:best_nonverbal_iq

```

Section `[pheno]` contains the list pheno DBs

```
dbs=ssc,vip
```

and the directory where Pheno Browser static data is located

```
browser_dir = %(wd)s/pheno/browser
```

Note also that for each pheno DB we have to specify measures for `age` and 
`nonverbal_iq`. The format used to specify these measures is following:

```
[instrument_name:]measure_name
```

For `SSC` pheno DB the age is a measure, that is located into an instrument 
`pheno_common`, so the specification is `pheno_common:age`. For `VIP` each
instrument has measure `measure.eval_age_months`, that specifies when the
instrument is applied and so we skip the `instrument_name` in specifing age
in `VIP`.


## Pheno Browser Data Preparation Tool

To prepare static data needed for Pheno Browser you need 
`prepare_pheno_browser.py`. Using

```
prepare_pheno_browser.py -h
```
will output some useful help for using the tool:

```
usage: prepare_pheno_browser.py [-h] [-v] [-p pheno_db] [-o output_dir]

USAGE

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         set verbosity level [default: None]
  -p pheno_db, --pheno_db pheno_db
                        phenotype DB to process
  -o output_dir, --output output_dir
                        ouput directory
```

The important part is that you need to specify the name of pheno DB you want
to work with and the output directory where you want to store the static files.

Example:
```
mkdir -p ssc_static
prepare_pheno_browser.py -p ssc -o ssc_static
```

