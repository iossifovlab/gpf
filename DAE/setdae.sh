

export PATH=${DAE_SOURCE_DIR}/tools:$PATH
export PATH=${DAE_SOURCE_DIR}/tests:$PATH
export PATH=${DAE_SOURCE_DIR}/annotation:$PATH
export PATH=${DAE_SOURCE_DIR}/annotation/tools:$PATH

export PATH=${SPARK_HOME}/bin:$PATH
export PYTHONPATH=${SPARK_HOME}/python:${DAE_SOURCE_DIR}:$PYTHONPATH

PS1="(variants) $PS1"
export PS1