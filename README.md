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
We recommend using [Anaconda environment](https://www.anaconda.com/)
for creation of GPF development environment.
In the steps below, we use the
[mamba](https://mamba.readthedocs.io/en/latest/index.html) package manager.

### Install GPF dependencies

Create a conda `gpf` environment with all of the conda package dependencies
from `environment.yml` and `dev-environment.yml` files. Update federation
environment if you plan to use federation. From `gpf` root directory run:

```bash
mamba env create --name gpf --file ./environment.yml
mamba env update --name gpf --file ./dev-environment.yml
```

To use this environment, you need to activate it using the following command:

```bash
conda activate gpf
```

The following commands are going to install GPF `dae` and `wdae` packages for
development usage. (You need to install GPF packages in the development `gpf`
conda environment.)

```bash
for d in dae wdae; do (cd $d; pip install -e .); done
```

### REST Client and Federation

If you want to work with GPF `federation` and `rest_client` modules you
will need to install additional dependencies:

```bash
mamba env update --name gpf --file ./federation/federation-environment.yml
```

After that you will need to install both modules:

```bash
pip install -e rest_client
pip install -e federation
```

### Additional GPF genotype storages

There are some additional genotype storages that are not included in the
default GPF installation and if you plan to use or develop features for these
genotype storages you need to install their dependencies.

#### Apache Impala genotype storage

To use ore develop features for GPF impala genotype storage you need some
additional dependencies installed. From `gpf` root directory update your `gpf`
conda environment using:

```bash
mamba env update --name gpf --file ./impala_storage/impala-environment.yml
```

and install the `gpf_impala_storage` package using:

```bash
pip install -e impala_storage
```

#### Apache Impala2 genotype storage

To use ore develop features for GPF impala genotype storage you need some
additional dependencies installed. From `gpf` root directory update your `gpf`
conda environment using:

```bash
mamba env update --name gpf --file ./impala2_storage/impala2-environment.yml
```

and install the `gpf_impala2_storage` package using:

```bash
pip install -e impala2_storage
```

#### GCP genotype storage

If you want support for genotype storage on Google Cloud Platform (GCP) using
the Google BigQuery for querying variants you need to install more dependencies
in your development environment:

```bash
mamba env update --name gpf --file ./gcp_storage/gcp-environment.yml
```

and install `gcp_genotype_storage` package using:

```bash
pip install -e gcp_storage
```

To run the tests you need to authenticate for `seqpipe-gcp-storage-testing`
project:

```bash
gcloud config list project
```

```
[core]
project = seqpipe-gcp-storage-testing

Your active configuration is: [default]
```

using

```bash
gcloud auth application-default login
```

To run the GCP storge tests you should enter into the
`gpf/gcp_storage` directory and run:

```bash
py.test -v gcp_storage/tests/
```

To run the intergration tests use:

```bash
py.test -v ../dae/tests/ --gsf gcp_storage/tests/gcp_storage.yaml
```

#### Pre-commit lint check hook

A git pre-commit hook for lint checking with Ruff is included.
To install it, run the following command from the repository's directory:

```bash
cp pre-commit .git/hooks
```

To bypass the pre-commit hook, use the following flag when committing:

```bash
git commit --no-verify
```
