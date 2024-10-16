#!/usr/bin/bash

# /opt/conda/bin/conda run --no-capture-output -n gpf \
#     /wd/scripts/wait-for-it.sh -h impala -p 8020 -t 300
# /opt/conda/bin/conda run --no-capture-output -n gpf \
#     /wd/scripts/wait-for-it.sh -h impala -p 21050 -t 300


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
    pheno_import --force -p comp_pheno.ped \
    -o $DAE_DB_DIR/pheno/comp_pheno \
    --force \
    -j 1 \
    -i instruments/ --data-dictionary comp_pheno_data_dictionary.tsv --pheno-id comp_pheno \
    --regression comp_pheno_regressions.conf \
    --person-column personId

mkdir -p $DAE_DB_DIR/pheno/images
cp -r $DAE_DB_DIR/pheno/comp_pheno/images/comp_pheno \
    $DAE_DB_DIR/pheno/images

cd /wd

cd /wd/integration/fixtures/hg19/micro_iossifov2014

/opt/conda/bin/conda run --no-capture-output -n gpf \
    simple_study_import --id iossifov_2014 \
    -o /wd/data/temp-remote \
    --denovo-file iossifov2014.txt \
    iossifov2014_families.ped

/opt/conda/bin/conda run --no-capture-output -n gpf \
    generate_denovo_gene_sets


cat >> /wd/data/data-hg19-remote/studies/iossifov_2014/iossifov_2014.yaml << EOT

phenotype_data: comp_pheno

phenotype_browser: true
phenotype_tool: true

enrichment:
  enabled: true
EOT

rm -rf $DAE_DB_DIR/wdae/wdae.sql
rm -rf $DAE_DB_DIR/wdae/wdae_django_pre.cache
rm -rf $DAE_DB_DIR/wdae/wdae_django_default.cache
/opt/conda/bin/conda run --no-capture-output -n gpf \
    /wd/wdae/wdae/wdaemanage.py migrate
/opt/conda/bin/conda run --no-capture-output -n gpf \
    /wd/wdae/wdae/wdae_create_dev_users.sh
/opt/conda/bin/conda run -n gpf \
    /wd/wdae/wdae/wdae_create_dev_federation_app.sh

/opt/conda/bin/conda run --no-capture-output -n gpf \
    grr_cache_repo --grr /wd/integration/grr_definition.yaml\
        --instance $DAE_DB_DIR/gpf_instance.yaml

while true; do

    /opt/conda/bin/conda run --no-capture-output -n gpf \
        /wd/wdae/wdae/wdaemanage.py runserver 0.0.0.0:21010
    sleep 10

done
