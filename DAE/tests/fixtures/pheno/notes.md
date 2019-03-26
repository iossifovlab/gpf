# Notes

## Import of pheno DB


```bash
pheno2DAE.py -p pheno1.ped -i instruments1/ -o pheno1.db
```

```bash
pheno2browser.py -p pheno1 -d pheno1.db -o browser/ --age "i1:age" --nonverbal_iq "i1:iq"
```