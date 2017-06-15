# Initial Setup Project Environment

## Download Anaconda

The GPF project uses Anaconda python distribution for *Python 2.7*. You need
to download Anaconda installer from *Continuum Analytics* 
[web site](https://www.continuum.io/downloads):

```
wget -c https://repo.continuum.io/archive/Anaconda2-4.4.0-Linux-x86_64.sh
```

After downloading the *Anaconda* installer you need to run the installer

```
bash Anaconda2-4.4.0-Linux-x86_64.sh
```

and follow the installer instructions.

## Install the GPF python environment

To install the GPF environment you need to use the environment description
file `root-anaconde-environment.yml` located into the root directory of the
project:

```
conda env update -f root-anaconda-environment.yml
```

## Prepare environment setup script

Example environment setup script is shown in the following snipped:

```
export PATH=$HOME/anaconda2/bin:$PATH       # path to your Anaconda installation

export DAE_SOURCE_DIR=$HOME/gpf/DAE         # path to GPF source
export DAE_DB_DIR=$HOME/data-dev            # path to GPF data directory


export PATH=${DAE_SOURCE_DIR}/tools:$PATH
export PATH=${DAE_SOURCE_DIR}/tests:$PATH
export PATH=${DAE_SOURCE_DIR}/../wvdb:$PATH
export PYTHONPATH=${DAE_SOURCE_DIR}:$PYTHONPATH
export PYTHONPATH=${DAE_SOURCE_DIR}/tools:$PYTHONPATH

PS1="(GPF) $PS1"
export PS1
```

When you are setting up your own environment you need to pay special attention
to:
* `PATH` where your own *Anaconda2* is installed;
* `DAE_SOURCE_DIR` where you cloned the source code of GPF system;
* `DAE_DB_DIR` where the GPF data is located.

## Example usage of conda

If you want to install specific version of a package you need to use:

```
conda install pysam=0.10.0
```

If the *bioconda* channel is not configured in your setup you need to use:
```
conda install -c bioconda pysam=0.10.0
```

If you need to search available version of a package in *bioconda* channel you
can use:
```
conda search -c bioconda pysam
```

If you want to add `bioconda` channel to default channels for your *Anaconda* 
setup you can use:
```
conda config --add channels bioconda
```