#!/bin/bash

wdaemanage.py createapplication --user 1 \
    --redirect-uris "http://gpf:8080/gpf/login http://localhost:8080/gpf/login" \
    --name "GPF Genotypes and Phenotypes in Families" \
    --client-id gpfjs  public authorization-code --skip-authorization
