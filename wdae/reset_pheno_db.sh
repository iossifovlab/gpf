#!/bin/bash

# echo 'DELETE FROM "pheno_db_valuefloat";' | ./manage.py dbshell
# echo 'DELETE FROM "pheno_db_variabledescriptor";' | ./manage.py dbshell

read -r -d '' drop_pheno_db << EOF
BEGIN;
DELETE FROM "pheno_db_variabledescriptor";
DELETE FROM "pheno_db_valuefloat";
DELETE FROM "pheno_db_individual";
COMMIT;
EOF

echo "$drop_pheno_db"

echo "$drop_pheno_db" | ./manage.py dbshell
