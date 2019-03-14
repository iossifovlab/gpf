GPF Getting Started Guide
=========================


Prerequisites [WIP]
###################

.. note::
    git
    wget
    gcc
    zlib

If you are using Ubuntu, you can run:

.. code-block:: bash

    sudo apt-get install git wget build-essential zlib1g-dev


Clone the GPF Repository
########################

To start using the GPF system, you need to clone the GPF source code repository
from Github:

.. code-block:: bash

    git clone --single-branch --branch variants git@github.com:seqpipe/gpf.git


Setup GPF Development Environment
#################################

The GPF system is developed in Python and supports both Python 2.7 and
Python 3.6. The recommended way to setup GPF development environment is to
use Anaconda.

Setup Anaconda Environment
++++++++++++++++++++++++++

Download and install Anaconda
*****************************

Download Anaconda from  Anaconda distribution page
(https://www.anaconda.com/distribution/):

.. code-block:: bash

    wget -c https://repo.anaconda.com/archive/Anaconda3-2018.12-Linux-x86_64.sh

and install it in your local environment, following the installer instructions:

.. code-block:: bash

    sh Anaconda3-2018.12-Linux-x86_64.sh

Create GPF environment
**********************

Most of the dependencies for GPF are described in Anaconda environment
description files located inside of the GPF source repository:

.. code-block:: bash

    gpf/python2-environment.yml
    gpf/python3-environment.yml

You can use these files to create a GPF Python development environment.
For example, if you want to create a Python 3 development conda environment,
use:

.. code-block:: bash

    conda env create -n gpf3 -f gpf/python3-environment.yml

To use this environment, you need to execute the following command:

.. code-block:: bash

    conda activate gpf3

Install ``pyarrow`` and ``pandas`` from Anaconda ``conda-forge`` channel:

.. code-block:: bash

    conda install -c conda-forge pyarrow pandas


Additionally, you will need to install `cyvcf2`. Clone the following
repository:

.. code-block:: bash

    git clone https://github.com/seqpipe/cyvcf2.git

Enter the `cyvcf2` directory and run pip install:

.. code-block:: bash

    cd cyvcf2
    pip install .
    cd ..


Install Spark
+++++++++++++

After creating a GPF environment, you should have Java JDK 8 installed in your
environment. Since Apache Spark runs on Java JDK 8, please verify your
version of Java JDK:

.. code-block:: bash

    java -version

...which should display something similar to the following:

.. code-block:: bash

    openjdk version "1.8.0_152-release"
    OpenJDK Runtime Environment (build 1.8.0_152-release-1056-b12)
    OpenJDK 64-Bit Server VM (build 25.152-b12, mixed mode)


Download Apache Spark distribution and extract it:

.. code-block:: bash

    wget -c https://www-us.apache.org/dist/spark/spark-2.4.0/spark-2.4.0-bin-hadoop2.7.tgz
    tar zxvf spark-2.4.0-bin-hadoop2.7.tgz

Start Apache Spark Thrift server:

.. code-block:: bash

    cd spark-2.4.0-bin-hadoop2.7/sbin
    ./start-thriftserver.sh


Get Startup Data Instance [WIP]
###############################

To start working with GPF, you will need a startup data instance. There are
two GPF startup instances that are aligned with different versions of the
reference human genome - for HG19 and HG38.

If you plan to work with variants aligned to the HG19 reference genome, you
will need a `data-hg19-startup` instance:

.. code-block:: bash

    rsync -avPHt -e "ssh -p 2020" --exclude ".dvc" --exclude ".git" \
        seqpipe@nemo.seqpipe.org:repo/data-hg19-startup .

This command will copy the necessary data into your working directory.

.. note::

    If you intend to make changes in this repo, it would be better to use::

        rsync -avPHt -e "ssh -p 2020" \
            seqpipe@nemo.seqpipe.org:repo/data-hg19-startup .

.. note::

    This data is available on `wigclust` in the following directory::

        /mnt/wigclust21/data/safe/chorbadj/GPF/data-hg19-startup

.. todo::

    We need to prepare GPF startup data instance for HG38.


Get Genomic Scores Database [TBD]
#################################

To annotate variants with genomic scores you will need a genomic scores
database.

There are two genomic scores databases - aligned to reference genomes HG19
and HG38.

You can download the full set of genomic scores or choose to download
only specific genomic scores you are interested in.

.. note::

    At the moment this data is available on `wigclust` in the following
    directories::

        /mnt/wigclust21/data/safe/chorbadj/genomics-scores/genomic-scores-hg19
        /mnt/wigclust21/data/safe/chorbadj/genomics-scores/genomic-scores-hg38


Update `setenv.sh` Script
#########################

Inside the GPF source directory, there is a file named
``setenv_template.sh``:

.. code-block:: bash

    # specifies where Apache Spark is installed
    export SPARK_HOME=<path to spark distribution>/spark-2.4

    # configure paths to genomic scores databases
    export DAE_GENOMIC_SCORES_HG19=<path to>/genomic-scores-hg19
    export DAE_GENOMIC_SCORES_HG38=<path to>/genomic-scores-hg38

    # specifies where the source directory for GPF DAE is
    export DAE_SOURCE_DIR=<path to gpf>/gpf/DAE
    # specifies the location of the GPF data instance
    export DAE_DB_DIR=<path to work data>/data-hg19

    # activates GPF conda environment
    conda activate gpf3

    # setups GPF paths
    source $DAE_SOURCE_DIR/setdae.sh

You should copy it as a separate file named ``setenv.sh`` and edit it according
you own setup. When you are ready, you need to source your ``setenv.sh`` file:

.. code-block:: bash

    source ./setenv.sh


Example Usage of GPF Python Interface
#####################################

Simplest way to start using GPF system python API is to import `variants_db`
object:

.. code-block:: python3

    from DAE import variants_db as vdb

This `vdb` factory object allows you to get all studies and datasets in the
configured GPF instance. For example to list all studies configured in
the startup GPF instance use:

.. code-block:: python3

    vdb.get_studies_ids()

that should return a list of all studies IDs:

.. code-block:: python3

    ['iossifov_2014',
    'iossifov_2014_small',
    'trio',
    'quad',
    'multi',
    'ivan']

To get specific study and query it you can use:

.. code-block:: python3

    st = vdb.get_study("trio")
    vs = st.query_variants()
    vs = list(vs)

.. note::
    `query_variants` method returns Python iterator.

To get the basic information about variants found by `query_variants` method
you can use:

.. code-block:: python3

    for v in vs:
        for aa in v.alt_alleles:
            print(aa)

    1:865582 C->T f1
    1:865583 G->A f1
    1:865624 G->A f1
    1:865627 G->A f1
    1:865664 G->A f1
    1:865691 C->T f1
    1:878109 C->G f1
    1:901921 G->A f1
    1:905956 CGGCTCGGAAGG->C f1
    1:1222518 C->A f1

The `query_variants` interface allows you to specify what kind of variants
you are interesetd in. For example if you need only 'missense' variants you
can use:

.. code-block:: python3

    st = vdb.get_study("iossifov_2014_small")
    vs = st.query_variants(effect_types=['missense'])
    vs = list(vs)
    print(len(vs))

    >> 6

Or if you are interested in 'missinse' variants only in people with role
'prb' you can use:

.. code-block:: python3

    vs = st.query_variants(effect_types=['missense'], roles='prb')
    vs = list(vs)
    len(vs)

    >> 3

For more information see:


Start GPF Web UI
################

Initial Setup of GPF Web UI
+++++++++++++++++++++++++++

Initial setup of GPF Web UI requires several steps:

* Initial setup of the local database to serve GFP Web UI. Since GPF Web UI is
    a Django application, it uses ``sqlite3`` for development purposes.
    To set it up, enter the ``gpf/wdae`` directory and run migrations::

        cd gpf/wdae
        ./manage.py migrate

* The next step is to create development users. Enter the
    ``gpf/wdae`` directory and run ``create_dev_users.sh``::

        ./create_dev_users.sh

    This script creates two users for development purposes -
    ``admin@iossifovlab.com`` and ``researche@iossifovlab.com``. The
    password for both users is ``secret``.


Start GPF Web UI
++++++++++++++++

To start the GPF Web UI, you need to run the Django development server.
Enter the ``gpf/wdae`` directory and run::

        ./manage.py runserver 0.0.0.0:8000


To check that everything works, you can open following URL in your browser::

    http://localhost:8000

.. note::
    If you run the development server on a computer that is different from your
    host machine, you should replace `localhost` with the name or IP of your
    server.

.. note::
    Before running your development server you will need a running Apache
    Spark Thrift server.

Import a Demo Dataset
#####################

In the GPF startup data instance there are a couple of demo studies:

    * `quad` with a couple of variants in a single quad family
    * `multi` with a couple of variants in a multigenerational family

.. note::
    You can download some more publicly available studies, which are prepared to be
    included into the GPF startup data instance.

To demonstrate how to import new study data into the GPF data instance, we
will reproduce the necessary steps for importing the `quad` study data.

Simple study import
+++++++++++++++++++

Usualy to import study data into GPF instance could take a lot of steps. To
make initial bootstraping easier you can use `simple_study_import.py` tool
that combines all the necessary steps in one tool.

Let say you have pedigree file `quad.ped` describing family information
and VCF file `quad.vcf` with variants.

To import this study into GPF instance:

* go into `studies` directory of GPF instance data folder::

        cd $DAE_DB_DIR/studies


* create a directory where you plan to save the imported data and enter inside
    that directory::

        mkdir quad1
        cd quad1


* run `simple_study_import.py` to import the data; this tool expects there
    arguments - study ID to use, pedigree file name and VCF file name::

        simple_study_import.py vcf quad1 ../quad/quad.ped ../quad/quad.vcf



Import a VCF Dataset
++++++++++++++++++++

The example data is located in the GPF startup data instance::

    cd data-hg19-startup/studies/quad/

This directory has the following structure::

    .
    ├── commonReport
    │   └── quad.json
    ├── quad
    │   ├── effect_gene.parquet
    │   ├── family.parquet
    │   ├── member.parquet
    │   ├── pedigree.parquet
    │   └── summary.parquet
    ├── quad.conf
    ├── quad.ped
    └── quad.vcf

The source data required for an import consists of:

*   a pedigree file, describing the family structure and inheritance
    relationships between sampled individuals; the ``quad.ped`` pedigree
    file content is::

        familyId personId dadId    momId    sex      status   role     phenotype
        f1       mom1     0        0        2        1        mom      unaffected
        f1       dad1     0        0        1        1        dad      unaffected
        f1       prb1     dad1     mom1     1        2        prb      autism
        f1       sib1     dad1     mom1     2        2        sib      autism

*   a VCF file containing variants; the content of the example variants file
    ``quad.vcf`` is::

        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">   
        ##contig=<ID=1>   
        ##contig=<ID=2>   
        #CHROM   POS      ID       REF      ALT      QUAL     FILTER   INFO     FORMAT   mom1     dad1     prb1     sib1
        1        11539    .        T        G        .        .        .        GT       0/1      0/0      0/1      0/0
        2        11540    .        T        G        .        .        .        GT       0/0      0/1      0/1      0/0

Importing this data into the GPF data instance means that you need to convert
pedigree and VCF data into the Apache Parquet format and annotate them with
variant effects and genomic scores. The default configuration for the
annotation is located in the GPF data instance. In the case of the GPF startup
data instance, the annotation configuration file is::

    data-hg19-startup/annotation.conf

The tool for converting VCF data to the Apache Parquet file format is
``vcf2parquet``. To run it you need to specify the pedigree file and the VCF
file you are converting. Additionally, you need to specify where the tool
should store the result files::

    cd data-hg19-startup/studies/quad/
    mkdir out
    vcf2parquet.py vcf quad.ped quad.vcf -o out/

After this command is finished, the result data should be stored in the
``out/`` directory::

    out/
    ├── effect_gene.parquet
    ├── family.parquet
    ├── member.parquet
    ├── pedigree.parquet
    └── summary.parquet


Configure Imported Data [WIP]
+++++++++++++++++++++++++++++

Minimal configuration for the newly imported data is as follows::

    [study]
    name = quad
    id = quad
    prefix = out/
    file_format = thrift
    phenotypes = autism

The ``id`` of the study should be unique in the GPF data instance,
``name`` is a human readable name of the study that will be used to display
the study in the GPF web UI.

.. todo::

    At the moment the GPF web UI works only with datasets, so you need
    to configure a minimal dataset representing the ``quad`` study. For this,
    you will need a ``quad.conf`` file inside
    ``data-hg19-startup/datasets``::

        [dataset]

        name = Quad Dataset
        id = quad_dataset
        phenotypes=autism
        studies = quad


Generate Variant Reports (optional)
+++++++++++++++++++++++++++++++++++

To generate families and de Novo variants report, you should use
`generate_common_reports.py`. This tool supports the option `--show-studies` to
list all studies and datasets configured in the GPF instance::

    generate_common_reports.py --show-studies

To generate the families and variants reports for a given configured study
or dataset, you
should use `--studies` option. For example, to generate the families and
variants reports for the `quad` study, you should use::

    generate_common_reports.py --studies quad


Generate Denovo Gene Sets (optional)
++++++++++++++++++++++++++++++++++++

To generate de Novo Gene sets, you should use the `generate_denovo_gene_sets.py`
tool. This tool supports the option  `--show-studies` to
list all studies and datasets configured in the GPF instance::

    generate_denovo_gene_sets.py --show-studies

To generate the de Novo gene sets for a given configured study
or dataset, you
should use `--studies` option. For example, to generate the de Novo
gene sets for the `quad` study, you should use::

    generate_denovo_gene_sets.py --studies quad


Start GPF Web UI
++++++++++++++++

After importing a new study into the GPF data instance, you need to restart the
GPF web UI. Stop the Django develompent server and start it again::

        ./manage.py runserver 0.0.0.0:8000

