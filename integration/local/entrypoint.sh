#!/usr/bin/bash

rm -rf /wd/data

mkdir -p /wd/data/data-hg19-local
mkdir -p /wd/data/data-hg19-remote

cp -r /wd/integration/local/data/* /wd/data/data-hg19-local/
cp -r /wd/integration/remote/data/* /wd/data/data-hg19-remote/


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

mkdir -p $DAE_DB_DIR/pheno/images
cp -r $DAE_DB_DIR/pheno/comp_pheno/browser/images/comp_pheno \
    $DAE_DB_DIR/pheno/


cd /wd/integration/fixtures/hg19/micro_iossifov2014

/opt/conda/bin/conda run --no-capture-output -n gpf \
    simple_study_import.py --id iossifov_2014 \
    -o /wd/temp \
    --denovo-file iossifov2014.txt \
    iossifov2014_families.ped

cd /wd

/opt/conda/bin/conda run --no-capture-output -n gpf \
    generate_denovo_gene_sets.py


cd /wd/dae_conftests

/opt/conda/bin/conda run --no-capture-output -n gpf \
    py.test -v dae_conftests/tests/test_setup.py
