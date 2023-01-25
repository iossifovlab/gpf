# GPF: Genotypes and Phenotypes in Families

The Genotype and Phenotype in Families (GPF) system manages large databases
of genetic variants and phenotypic measurements obtained from collections
of families and individual family members.

The main application of the system has been in managing the data gathered from
the Simons Simplex Collection, a collection of ~2,600 families with one child
diagnosed with autism.

Information on how to use GPF can be found in the
[GPF documentation](https://iossifovlab.com/gpfuserdocs/).

## Development
We recommend using 
[Anaconda environment](https://www.anaconda.com/)](https://www.anaconda.com/) 
for creation of GPF development environment.

### Install GPF dependencies

Create a conda `gpf` environment with all of the conda package dependencies
from `environment.yml` and `dev-environment.yml` files:

```bash
mamba env create --name gpf --file ./environment.yml
mamba env update --name gpf --file ./dev-environment.yml
```

To use this environment, you need to activate it using the following command:

```bash
conda activate gpf
```

The following commands are going to install GPF dae and wdae packages for
development usage. (You need to install GPF packages in the development
conda environment.)

```bash
for d in dae wdae dae_conftests; do (cd $d; pip install -e .); done
```

If you want support for genotype storage on Google Cloud Platform using the
Google BigQuery for querying variants you need to install more dependencies
in your development environment:

```bash
mamba env update --name gpf --file ./gcp_genotype_storage/environment.yml
```

and install `gcp_genotype_storage` package using:

```bash
pip install -e gcp_genotype_storage
```

