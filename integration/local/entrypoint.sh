#!/usr/bin/bash

rm -rf /wd/data

mkdir -p /wd/data/data-hg19-local
mkdir -p /wd/data/data-hg19-remote

cp -r /wd/integration/local/data/* /wd/data/data-hg19-local/
cp -r /wd/integration/remote/data/* /wd/data/data-hg19-remote/


for d in /wd/dae /wd/wdae /wd/dae_conftests; do
    cd ${d};
    /opt/conda/bin/conda run --no-capture-output -n gpf pip install -e .
done

cd /wd/integration/fixtures/pheno/comp-data

/opt/conda/bin/conda run --no-capture-output -n gpf \
    pheno_import --force -p comp_pheno.ped \
    -o $DAE_DB_DIR/pheno/comp_pheno
    -i instruments/ -d comp_pheno_data_dictionary.tsv --pheno-id comp_pheno \
    --regression comp_pheno_regressions.conf \
    --person-column personId

mkdir -p $DAE_DB_DIR/pheno/images
cp -r $DAE_DB_DIR/pheno/comp_pheno/browser/images/comp_pheno \
    $DAE_DB_DIR/pheno/


cd /wd/integration/fixtures/hg19/micro_iossifov2014

/opt/conda/bin/conda run --no-capture-output -n gpf \
    simple_study_import.py --id iossifov_2014 \
    -o /wd/temp-local \
    --denovo-file iossifov2014.txt \
    iossifov2014_families.ped

cd /wd

/opt/conda/bin/conda run --no-capture-output -n gpf \
    generate_denovo_gene_sets.py

chmod -R 0777 $DAE_DB_DIR
echo "sample description" > $DAE_DB_DIR/main_description.md
echo "about description" > $DAE_DB_DIR/about_description.md
