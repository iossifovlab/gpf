

## Development environment

```
conda env create -n gpf -f conda-environment.yml
```

Activate the environment:
```
source activate gpf
```

Install seqpipe version of `cyvcf2`:
```
pip install git+https://github.com/seqpipe/cyvcf2.git
```

Overwrite installed version of `thrift`:

```
pip install thrift==0.9.3
```


## Script to setup development environment

Use `setenv-template.sh` to create your `setenv.sh`:

```
export SPARK_HOME=<path to local direcory with spark-2.2 distribution>


export DAE_SOURCE_DIR=<path to local gpf>/DAE
export DAE_DB_DIR=<path to local data dir>/data-hg19


export PATH=${DAE_SOURCE_DIR}/tools:$PATH
export PATH=${DAE_SOURCE_DIR}/tests:$PATH
export PATH=${DAE_SOURCE_DIR}/annotation_pipeline:$PATH

export PYTHONPATH=${DAE_SOURCE_DIR}:$PYTHONPATH
export PYTHONPATH=${DAE_SOURCE_DIR}/tools:$PYTHONPATH

source activate gpf

PS1="(variants) $PS1"
export PS1
```