#!/usr/bin/bash


for d in /wd/dae /wd/wdae /wd/dae_conftests; do
    cd ${d};
    /opt/conda/bin/conda run --no-capture-output -n gpf pip install -e .
done

mkdir -p /wd/data/data-hg19-remote
cp -r /wd/integration/remote/data/* /wd/data/data-hg19-remote/

cd /wd/integration/fixtures/pheno/comp-data

/opt/conda/bin/conda run --no-capture-output -n gpf \
    import_phenotypes --force import_project.yaml

/opt/conda/bin/conda run --no-capture-output -n gpf \
    build_pheno_browser --force comp_pheno

cd /wd

cd /wd/integration/fixtures/hg19/micro_iossifov2014

/opt/conda/bin/conda run --no-capture-output -n gpf \
    simple_study_import --id iossifov_2014 \
    -o /wd/data/temp-remote \
    --denovo-file iossifov2014.txt \
    --denovo-location location \
    --denovo-variant variant \
    --denovo-family-id familyId \
    --denovo-best-state bestState \
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
