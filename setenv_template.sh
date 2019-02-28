

# specifies where Apache Spark is installed
export SPARK_HOME=<path to spark distribution>/spark-2.4


# configure paths to genomics scores databases
export DAE_GENOMIC_SCORES_HG19=<path to>/genomic-scores-hg19
export DAE_GENOMIC_SCORES_HG38=<path to>/genomic-scores-hg38


# specifies where is the source directory for GPF DAE
export DAE_SOURCE_DIR=<path to gpf>/gpf/DAE
# specifies the location of GPF data instance
export DAE_DB_DIR=<path to work data>/data-hg19

# activates GPF conda environment
conda activate gpf3

# setups GPF paths
source $DAE_SOURCE_DIR/setenv.sh

