#!/bin/sh

echo "jenkins_data DataHG19Branch: ${DataHG19StartupBranch}"
echo "jenkins_data DAE_DB_DIR: ${DAE_DB_DIR}"

git clone git@github.com:seqpipe/data-hg19-startup.git

cd $DAE_DB_DIR

git checkout -f ${DataHG19Branch}
git pull origin ${DataHG19Branch}

dvc pull -r nemo -j 20
rm -rf enrichment/cache/*
rm -rf geneInfo/cache/*

cd -


cd $DAE_DB_DIR/pheno

for pheno_db in "comp_pheno" "comp_pheno_data"
do

    echo $pheno_db
    cd $pheno_db
    rm -rf ${pheno_db}
    tar zxf "${pheno_db}_pheno_browser.tar.gz"
    cd ..
    pwd
done

cd -
