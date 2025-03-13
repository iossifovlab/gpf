# Notes

## Import of pheno DB


```bash
pheno2dae.py -p comp_pheno.ped -i instruments/ -d comp_pheno_data_dictionary.tsv -o comp_pheno.db
```


```bash
pheno2browser.py -p comp_pheno -d comp_pheno/comp_pheno.db -o comp_pheno/browser --regression comp_pheno_regressions.conf
```
