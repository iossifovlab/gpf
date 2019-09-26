#!/bin/bash

set -e

REFERENCE_GENOME=$1
INSTALL_DIRNAME=$2

if [[ -z $REFERENCE_GENOME ]]; then
    REFERENCE_GENOME=hg19
fi

if [[ $REFERENCE_GENOME != 'hg19' &&  $REFERENCE_GENOME != 'hg38' ]]; then
    echo "ERROR: Unsupported reference genome: $REFERENCE_GENOME. Exiting..."
    exit 1
fi

if [[ -z $INSTALL_DIRNAME ]]; then
    export INSTALL_DIRNAME=data-${REFERENCE_GENOME}-startup
fi

export CONDA_ENV=$(conda env list | grep "*" | sed "s/[[:space:]]\+/\t/g" | cut -f 3)
echo "Active conda environment: $CONDA_ENV"


echo "Bootstrapping GPF into '$INSTALL_DIRNAME'"

if [[ -d "${INSTALL_DIRNAME}" ]]; then
    echo "ERROR: Directory $INSTALL_DIRNAME alreay exists. Exiting..."
    exit 1
fi



DATA_ARCHIVE=data-${REFERENCE_GENOME}-startup-latest.tar.gz


wget -c https://iossifovlab.com/distribution/public/$DATA_ARCHIVE

mkdir $INSTALL_DIRNAME && \
    tar xzf $DATA_ARCHIVE -C $INSTALL_DIRNAME --strip-components 1

rm $DATA_ARCHIVE

cd $INSTALL_DIRNAME
export DAE_DB_DIR=`pwd`
echo "GPF data directory in use: $DAE_DB_DIR"

mkdir -p genomic-scores-hg19
mkdir -p genomic-scores-hg38

mkdir wdae

cat <<EOF > setenv.sh
#!/bin/bash

conda activate ${CONDA_ENV}

export DAE_DB_DIR=$DAE_DB_DIR
export DAE_GENOMIC_SCORES_HG19=$DAE_DB_DIR/genomic-scores-hg19
export DAE_GENOMIC_SCORES_HG38=$DAE_DB_DIR/genomic-scores-hg38

EOF

cd wdae

wdaemanage.py migrate
wdaemanage.py user_create admin@iossifovlab.com -p secret -g any_dataset:admin
wdaemanage.py user_create research@iossifovlab.com -p secret

cd -
