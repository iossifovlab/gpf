#!/bin/bash
# Script intended for running the WDAE django server on the test remote

pip install -e /code/dae
pip install -e /code/wdae

if [ -f "/data/studies/iossifov_2014/iossifov_2014.conf" ]; then
    echo "Studies found"
else
    echo "Studies missing, importing..."
    /code/dae/dae/tools/simple_study_import.py /study/IossifovWE2014.ped --denovo-file /study/IossifovWE2014.tsv --id iossifov_2014
    echo -e "\n[enrichment]\nenabled = true" >> /data/studies/iossifov_2014/iossifov_2014.conf
    echo "Done"
fi

if [ -f "/data/pheno/comp_pheno/comp_pheno.conf" ]; then
    echo "Phenotype data found"
else
    echo "Phenotype data missing, importing..."
    PHENO_DIR="/code/comp-data"
    /code/dae/dae/tools/simple_pheno_import.py \
        -p ${PHENO_DIR}/comp_pheno.ped \
        -d ${PHENO_DIR}/comp_pheno_data_dictionary.tsv \
        -i ${PHENO_DIR}/instruments/ \
        -o comp_pheno \
        --regression ${PHENO_DIR}/comp_pheno_regressions.conf
    sed -i '5i\\nphenotype_data="comp_pheno"' /data/studies/iossifov_2014/iossifov_2014.conf
fi

/code/wdae/wdae/wdaemanage.py migrate
/code/wdae/wdae/wdae_create_dev_users.sh
/code/wdae/wdae/wdaemanage.py runserver 0.0.0.0:21010
