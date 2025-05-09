#!/bin/bash

wdaemanage.py createapplication --user 1 \
    --redirect-uris "http://localhost:4200/login" \
    --name "GPF Genotypes and Phenotypes in Families" \
    --client-id gpfjs  public authorization-code --skip-authorization