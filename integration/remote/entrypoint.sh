#!/usr/bin/bash

/opt/conda/bin/conda run --no-capture-output -n gpf \
    /wd/scripts/wait-for-it.sh -h impala -p 8020 -t 300
/opt/conda/bin/conda run --no-capture-output -n gpf \
    /wd/scripts/wait-for-it.sh -h impala -p 21050 -t 300


for d in /wd/dae /wd/wdae /wd/dae_conftests; do
    cd ${d};
    /opt/conda/bin/conda run --no-capture-output -n gpf pip install -e .
done

while :
do
    if [[ -f "$DAE_DB_DIR/gpf_instance.yaml" ]]; then
        break
    fi
    sleep 1
done

cd /wd/integration/fixtures/pheno/comp-data

/opt/conda/bin/conda run --no-capture-output -n gpf \
    simple_pheno_import.py --force -p comp_pheno.ped \
    -i instruments/ -d comp_pheno_data_dictionary.tsv -o comp_pheno \
    --regression comp_pheno_regressions.conf

mkdir -p $DAE_DB_DIR/pheno/images
cp -r $DAE_DB_DIR/pheno/comp_pheno/browser/images/comp_pheno \
    $DAE_DB_DIR/pheno/

cd /wd

cd /wd/integration/fixtures/hg19/micro_iossifov2014

/opt/conda/bin/conda run --no-capture-output -n gpf \
    simple_study_import.py --id iossifov_2014 \
    -o /wd/temp \
    --denovo-file iossifov2014.txt \
    iossifov2014_families.ped

/opt/conda/bin/conda run --no-capture-output -n gpf \
    generate_denovo_gene_sets.py


/opt/conda/bin/conda run --no-capture-output -n gpf \
    /wd/wdae/wdae/wdaemanage.py migrate
/opt/conda/bin/conda run --no-capture-output -n gpf \
    /wd/wdae/wdae/wdae_create_dev_users.sh

/opt/conda/bin/conda run --no-capture-output -n gpf \
    grr_cache_repo --definition /wd/integration/grr_definition.yaml\
        --instance $DAE_DB_DIR/gpf_instance.yaml

/opt/conda/bin/conda run --no-capture-output -n gpf \
    /wd/wdae/wdae/wdaemanage.py runserver 0.0.0.0:21010