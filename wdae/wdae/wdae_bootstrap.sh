#!/bin/bash

DATA_ARCHIVE=data-hg19-startup-latest.tar.gz
INSTALL_DIRNAME=$1

if [ -z $INSTALL_DIRNAME ]; then
    export INSTALL_DIRNAME=data-hg19-startup
fi

if [ -d '$INSTALL_DIRNAME' ];
then
    echo "Directory $INSTALL_DIRNAME alreay exists. Exiting..."
    exit 1
fi

echo "Bootstrapping GPF into '$INSTALL_DIRNAME'"

wget -c https://iossifovlab.com/distribution/public/$DATA_ARCHIVE

mkdir $INSTALL_DIRNAME && \
    tar xzf $DATA_ARCHIVE -C $INSTALL_DIRNAME --strip-components 1

# rm $DATA_ARCHIVE

cd $INSTALL_DIRNAME
export DAE_DB_DIR=`pwd`
echo "GPF data directory in use: $DAE_DB_DIR"

mkdir -p genomic-scores-hg19
mkdir -p genomic-scores-hg38

mkdir wdae
cd wdae

wdaemanage.py migrate
wdaemanage.py user_create admin@iossifovlab.com -p secret -g any_dataset:admin
wdaemanage.py user_create research@iossifovlab.com -p secret

cat <<EOF > setenv.sh
#!/bin/bash

export DAE_DB_DIR=$DAE_DB_DIR
export DAE_GENOMIC_SCORES_HG19=$DAE_DB_DIR/genomic-scores-hg19
export DAE_GENOMIC_SCORES_HG38=$DAE_DB_DIR/genomic-scores-hg38

EOF

cd -
