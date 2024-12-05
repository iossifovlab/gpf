#!/usr/bin/bash


for d in /wd/dae /wd/wdae; do
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

cd /wd

rm -rf $DAE_DB_DIR/wdae/wdae.sql
rm -rf $DAE_DB_DIR/wdae/wdae_django_pre.cache
rm -rf $DAE_DB_DIR/wdae/wdae_django_default.cache

cd /wd/rest_client/integration/fixtures/micro_iossifov2014

/opt/conda/bin/conda run --no-capture-output -n gpf \
    simple_study_import --id iossifov_2014 \
    -o /wd/data/temp-resttest \
    --denovo-file iossifov2014.txt \
    iossifov2014_families.ped

/opt/conda/bin/conda run --no-capture-output -n gpf \
    generate_denovo_gene_sets

/opt/conda/bin/conda run --no-capture-output -n gpf \
    /wd/wdae/wdae/wdaemanage.py migrate
/opt/conda/bin/conda run --no-capture-output -n gpf \
    wdaemanage.py user_create admin@iossifovlab.com \
    -p secret -g any_dataset:any_user:admin || true
/opt/conda/bin/conda run --no-capture-output -n gpf \
    wdaemanage.py user_create research@iossifovlab.com \
    -p secret -g any_user || true

/opt/conda/bin/conda run -n gpf \
    wdaemanage.py createapplication \
        confidential client-credentials \
        --user 1 \
        --redirect-uris "http://resttest:21011/login" \
        --name "testing rest client app1" \
        --client-id resttest1 \
        --client-secret secret \
        --skip-authorization

/opt/conda/bin/conda run --no-capture-output -n gpf \
    grr_cache_repo --grr /wd/rest_client/integration/grr_definition.yaml\
        --instance $DAE_DB_DIR/gpf_instance.yaml

while true; do

    /opt/conda/bin/conda run --no-capture-output -n gpf \
        /wd/wdae/wdae/wdaemanage.py runserver 0.0.0.0:21011
    sleep 10

done
