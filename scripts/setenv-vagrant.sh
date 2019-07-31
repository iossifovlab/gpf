export DAE_GENOMIC_SCORES_HG19=/genomic-scores-hg19
export DAE_GENOMIC_SCORES_HG38=/genomic-scores-hg38

export DAE_HDFS_HOST=localhost
export DAE_HDFS_PORT=8020

export DAE_IMPALA_HOST=localhost
export DAE_IMPALA_PORT=21050

export PATH=${DAE_SOURCE_DIR}/tools:$PATH
export PATH=${DAE_SOURCE_DIR}/tests:$PATH
export PATH=${DAE_SOURCE_DIR}/annotation:$PATH
export PATH=${DAE_SOURCE_DIR}/annotation/tools:$PATH

export PYTHONPATH=${DAE_SOURCE_DIR}:$PYTHONPATH

conda activate gpf

export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64

export HADOOP_HOME=/opt/hadoop
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
export PATH=$HADOOP_HOME/bin:$PATH
export LD_LIBRARY_PATH=$HADOOP_HOME/lib/native$LD_LIBRARY_PATH

export CLASSPATH=`$HADOOP_HOME/bin/hadoop classpath --glob`
