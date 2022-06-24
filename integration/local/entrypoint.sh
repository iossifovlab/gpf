#!/usr/bin/bash

/opt/conda/bin/conda run --no-capture-output -n gpf \
    /wd/scripts/wait-for-it.sh -h impala -p 8020 -t 300
/opt/conda/bin/conda run --no-capture-output -n gpf \
    /wd/scripts/wait-for-it.sh -h impala -p 21050 -t 300


for d in /wd/dae /wd/wdae /wd/dae_conftests; do
    cd ${d};
    /opt/conda/bin/conda run --no-capture-output -n gpf pip install -e .
done

cd /wd/integration/fixtures/pheno/comp-data

/opt/conda/bin/conda run --no-capture-output -n gpf \
    simple_pheno_import.py --force -p comp_pheno.ped \
    -i instruments/ -d comp_pheno_data_dictionary.tsv -o comp_pheno \
    --regression comp_pheno_regressions.conf

mkdir -p /wd/integration/local/data/pheno/images
cp -r /wd/integration/local/data/pheno/comp_pheno/browser/images/comp_pheno \
    /wd/integration/local/data/pheno/


cd /wd/integration/fixtures/hg19/micro_iossifov2014

/opt/conda/bin/conda run --no-capture-output -n gpf \
    simple_study_import.py --id iossifov_2014 \
    -o /wd/temp \
    --denovo-file iossifov2014.txt \
    iossifov2014_families.ped

cd /wd

/opt/conda/bin/conda run --no-capture-output -n gpf \
    generate_denovo_gene_sets.py

