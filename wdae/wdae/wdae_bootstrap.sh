#!/bin/bash

DATA_ARCHIVE=data-hg19-startup-3.0.0dev22.tar.gz
INSTALL_DIRNAME=$1

if [ -z $INSTALL_DIRNAME ]; then
    export INSTALL_DIRNAME=data-hg19-startup
fi

echo "Bootstrapping GPF into '$INSTALL_DIRNAME'"

wget -c -q https://iossifovlab.com/distribution/public/$DATA_ARCHIVE

mkdir $INSTALL_DIRNAME && \
    tar xzf $DATA_ARCHIVE -C $INSTALL_DIRNAME --strip-components 1

rm $DATA_ARCHIVE

cd $INSTALL_DIRNAME
DAE_DB_DIR=`pwd`
echo "GPF data directory in use: $DAE_DB_DIR"

mkdir wdae
cd wdae

wdaemanage.py migrate
wdaemanage.py user_create admin@iossifovlab.com -p secret -g any_dataset:admin
wdaemanage.py user_create research@iossifovlab.com -p secret

cd -

cat <<EOF > setenv.sh
#!/bin/bash

export DAE_DB_DIR=$DAE_DB_DIR

EOF
