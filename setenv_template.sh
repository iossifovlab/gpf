
export SPARK_HOME=<path to spark distribution>/spark-2.2


export DAE_SOURCE_DIR=<path to gpf>/gpf/DAE

export DAE_DB_DIR=<path to work data>/data-hg19


export PATH=${DAE_SOURCE_DIR}/tools:$PATH
export PATH=${DAE_SOURCE_DIR}/tests:$PATH
export PATH=${DAE_SOURCE_DIR}/annotation_pipeline:$PATH

export PYTHONPATH=${DAE_SOURCE_DIR}:$PYTHONPATH
export PYTHONPATH=${DAE_SOURCE_DIR}/tools:$PYTHONPATH

source activate gpf

PS1="(variants) $PS1"
export PS1
