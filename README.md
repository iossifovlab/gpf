# GPF: Genotypes and Phenotypes in Families

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

The Genotype and Phenotype in Families (GPF) system manages large databases
of genetic variants and phenotypic measurements obtained from collections
of families and individual family members.

The main application of the system has been in managing the data gathered from
the Simons Simplex Collection, a collection of ~2,600 families with one child
diagnosed with autism.

Information on how to use GPF can be found in the [GPF documentation](https://iossifovlab.com/gpfuserdocs/).

## Development

We recommend to use [Anaconda environment](https://www.anaconda.com/) as a GPF
development environment.

We use [pre-commit](https://pre-commit.com/) to enforce formatting and type checking.
It is included in the conda package dependencies below.
Once you have cloned the repository, run the following command within it to install the hooks:
```bash
pre-commit install
```

### Install GPF dependencies

Create a conda `gpf` environment with all of the conda package dependencies
from `conda-environment.yml` file:

```bash
conda create \
    -c defaults -c conda-forge  -c iossifovlab -c bioconda \
    -n gpf_dev \
    --file conda-environment.yml
```

To use this environment, you need to activate it using the following command:

```bash
conda activate gpf_dev
```

If the envirnoment you want to work in is already activeated run:
```bash
conda install \
    -c defaults -c conda-forge  -c iossifovlab -c bioconda \
    --file conda-environment.yml
```

These commands are going to install GPF dae and wdae packages for development
usage. (You need to install GPF packages in the conda environment.)

```bash
for d in dae wdae dae_conftests; do (cd $d; pip install -e .); done
```

### Bootstrap GPF

To start working with GPF, you will need a data instance. You can get one from
the GPF startup instances which are aligned with different versions of the
reference human genome - HG19 and HG38.

Besides the data instance some initial bootstrapping of GPF is also necessary.

To make bootstrapping easier, the script `wdae_bootstrap.sh` is provided,
which prepares GPF for initial start.

The bootstrap script creates a working directory where the data will be
stored. You can provide the name of the working directory as a parameter
to the boostrap script. For example, if you want the working directory to
be named `gpf_test`, use the following command:

* For HG19:
    ```bash
    wdae_bootstrap.sh hg19 gpf_test
    ```

* For HG38
    ```bash
    wdae_bootstrap.sh hg38 gpf_test
    ```

In addition to the conda environment you also need to set some environment
variables. You can find a sample file containing these environment variables in
the startup data instance - `gpf_test/setenv.sh`. To activate it you need to:

```bash
cd gpf_test/
source ./setenv.sh
cd -
```

Now you are ready to contribute to the GPF project.
