# Notes

## Import of pheno DB


```bash
pheno2dae.py -p pheno.ped -i instruments/ -o pheno.db
```

```bash
pheno2dae.py -p pheno.ped -i instruments/ -d descriptions_valid.tsv -o pheno.db
```

```bash
pheno2browser.py -p pheno -d pheno.db -o browser/ --age "i1:age" --nonverbal_iq "i1:iq"
```

## Add default filter to a measure

Following script adds a default filter to instrument 1's measure 10.

```sql
UPDATE measure
SET default_filter='< 9000'
WHERE measure_id='i1.m10';
```
