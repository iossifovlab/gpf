#!/usr/bin/env bash

export WD=$(pwd)

pip install -e ${WD}/dae
pip install -e ${WD}/wdae

# create GPF instance
mkdir -p ${WD}/.tmp/data/data-hg38-hello
cat > ${WD}/.tmp/data/data-hg38-hello/gpf_instance.yaml << EOT
instance_id: "hg38_hello"

reference_genome:
    resource_id: "hg38/genomes/GRCh38-hg38"

gene_models:
    resource_id: "hg38/gene_models/refSeq_v20200330"
EOT

mkdir -p ${WD}/.tmp/data/cache
touch ${WD}/.tmp/data/cache/grr_definition.yaml
cat > ${WD}/.tmp/data/cache/grr_definition.yaml << EOT
id: "default"
type: "url"
url: "https://grr.seqpipe.org/"
cache_dir: "/wd/cache/grrCache"
EOT

export DAE_DB_DIR="${WD}/.tmp/data/data-hg38-hello"

wdaemanage migrate
wdaemanage user_create admin@iossifovlab.com -p secret -g any_dataset:admin || true

# clean up old docs build
rm -rf ${WD}/docs/_build

# generate docs
sphinx-apidoc ${WD}/dae/dae -o docs/dae/modules/ -f 

sphinx-apidoc ${WD}/wdae/wdae -o docs/wdae/modules/ -f 

${WD}/docs/wdae/api_docs_generator.py \
    --root_dir ${WD}/wdae/wdae \
    --output_dir ${WD}/docs/wdae/routes


cd ${WD}/docs/
sphinx-build -b html . _build/html

# archive docs
tar -czf ${WD}/docs/gpf-html.tar.gz -C _build/ html/
