GPF Getting Started Guide
=========================


Prerequisites [WIP]
###################

    git
    wget
    gcc
    zlib

If you are using Ubuntu, you can run:

.. code-block:: bash

    sudo apt-get install git wget build-essential zlib1g-dev


Clone the GPF Repository
########################

To start using GPF system you need to clone the GPF source code repository
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

Download Anaconda from  Anaconda distribution page (https://www.anaconda.com/distribution/)

.. code-block:: bash

    wget -c https://repo.anaconda.com/archive/Anaconda3-2018.12-Linux-x86_64.sh

and install it in your local environment following the installer instructions:

.. code-block:: bash

    sh Anaconda3-2018.12-Linux-x86_64.sh

Create GPF environment
**********************

Most of dependencies for GPF are described into Anaconda environmet description
files located inside of the GPF source repository:

.. code-block:: bash

    gpf/python2-environment.yml
    gpf/python3-environment.yml

You can use these files to create an GPF python development environment.
For example if you want to create Python 3 development conda environment, use:

.. code-block:: bash

    conda env create -n gpf3 -f gpf/python3-environment.yml

To use this environment you need to execute the following command:

.. code-block:: bash

    conda activate gpf3

Install ``pyarrow`` and ``pandas`` from Anaconda ``conda-forge`` channel:

.. code-block:: bash

    conda install -c conda-forge pyarrow pandas


Additionally you will need to install `cyvcf2`. To this end clone this repo:

.. code-block:: bash

    git clone https://github.com/seqpipe/cyvcf2.git

Enter inside `cyvcf2` directory and run pip install:

.. code-block:: bash

    cd cyvcf2
    pip install .
    cd ..


Install Spark
+++++++++++++

After creating a GPF environmet you should have Java JDK 8 installed into your
environment. Since Apache Spark runs on Java JDK 8, please verify your
version of Java JDK:

.. code-block:: bash

    java -version

should display something similar to the following:

.. code-block:: bash

    openjdk version "1.8.0_152-release"
    OpenJDK Runtime Environment (build 1.8.0_152-release-1056-b12)
    OpenJDK 64-Bit Server VM (build 25.152-b12, mixed mode)


Download Apache Spark distribution and unarchive it:

.. code-block:: bash

    wget -c https://www-us.apache.org/dist/spark/spark-2.4.0/spark-2.4.0-bin-hadoop2.7.tgz
    tar zxvf spark-2.4.0-bin-hadoop2.7.tgz

Start Apache Spark Thrift server:

.. code-block:: bash

    cd spark-2.4.0-bin-hadoop2.7/sbin
    ./start-thriftserver.sh


Get Startup Data Instance [WIP]
###############################

To start working with GPF you will need a startup data instance. There are
two GPF startup instances that are aligned with different versions of the
reference Humman genome - for HG19 and HG38.

If you plan to work with variants alligned to HG19 reference genome, you
will need `data-hg19-startup` instance. To get it you will need rsync:

.. code-block:: bash

    rsync -avPHt -e "ssh -p 2020" --exclude ".dvc" --exclude ".git" \
        seqpipe@nemo.seqpipe.org:repo/data-hg19-startup .

This command will copy the necessary data into your working directory.

.. note::

    To make changes into this repo would be better to use::

        rsync -avPHt -e "ssh -p 2020" \
            seqpipe@nemo.seqpipe.org:repo/data-hg19-startup .

.. note::

    This data is available on `wigclust` into following directory::

        /mnt/wigclust21/data/safe/chorbadj/GPF/data-hg19-startup

.. todo::

    We need to prepare GPF startup data instance for HG38.


Get Genomic Scores Database [TBD]
#################################

To annotate variants with genomic scores you will need this genomic scores.

There are two genomic scores databases aligned to both reference genomes HG19
and HG38.

You can download full set of genomic scores databases or choose to download
only specific genomic scores you are interested in.

.. note::

    At the moment this data is available on `wigclust` into following
    directories::

        /mnt/wigclust21/data/safe/chorbadj/genomics-scores/genomic-scores-hg19
        /mnt/wigclust21/data/safe/chorbadj/genomics-scores/genomic-scores-hg38


Update `setenv.sh` Script
#########################

Inside GPF source directory there is a file named
``setenv_template.sh``:

.. code-block:: bash

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

You shoud copy it as ``setenv.sh`` file and edit it according you own setup.
When you are ready you need to source your ``setenv.sh`` file:

.. code-block:: bash

    source ./setenv.sh


Example Usage of GPF Python Interface
#####################################


Start GPF Web UI
################

Initial Setup of GPF Web UI
+++++++++++++++++++++++++++

Initial setup of GPF Web UI requires several steps:

* Inital setup of the local database to serve GFP Web UI. Since GPF Web UI is
    an Django application, it uses ``sqlite3`` for development purposes.
    To setup it go into ``gpf/wdae`` directory and run migrations:

    .. code-block:: bash

        cd gpf/wdae
        ./manage.py migrate

* Next step is to create development users. To this end from inside
    ``gpf/wdae`` directory run ``create_dev_users.sh``:

    .. code-block:: bash

        ./create_dev_users.sh

    This scripts creates two users for development purposes that are
    ``admin@iossifovlab.com`` and ``researche@iossifovlab.com`` that have
    password ``secret``.


Start GPF Web UI
++++++++++++++++

To start the GPF Web UI you need to run Django development server. To this end
enter into ``gpf/wdae`` directory and run:

    .. code-block:: bash

        ./manage.py runserver 0.0.0.0:8000


To check that everything works you can open following URL in your browser::

    http://localhost:8000

.. note::
    If you run the development server on a computer that is different from your
    host machine, the you should replace `localhost` with the name or IP of your
    server.


Import a Demo Dataset
#####################

In the GPF startup data instance there are a couple demo studies:

    * `quad` with couple of variants into single quad family
    * `multi` with couple of variants into multigenerational family

.. note::
    You can download some more publicly available studies, prepared to be
    included into GPF startup data instance.

To demonstrate how to import new study data into the GPF data instance we
will reproduce the neccessary step for importing `quad` study data.

Import a VCF Dataset
++++++++++++++++++++

The example data is located into GPF startup data instance::

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

The source data required for import consists of:

*   a pedigree file, describing the family structure and inheritance
    relationships between sampled individuals; the ``quad.ped`` pedigree
    file content is::

        familyId personId dadId    momId    sex      status   role     phenotype
        f1       mom1     0        0        2        1        mom      unaffected
        f1       dad1     0        0        1        1        dad      unaffected
        f1       prb1     dad1     mom1     1        2        prb      autism
        f1       sib1     dad1     mom1     2        2        sib      autism

*   a VCF file containing variants; the example variants file ``quad.vcf``
    content is::

        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">   
        ##contig=<ID=1>   
        ##contig=<ID=2>   
        #CHROM   POS      ID       REF      ALT      QUAL     FILTER   INFO     FORMAT   mom1     dad1     prb1     sib1
        1        11539    .        T        G        .        .        .        GT       0/1      0/0      0/1      0/0
        2        11540    .        T        G        .        .        .        GT       0/0      0/1      0/1      0/0

Importing this data into GPF data instance means that you need to convert
pedigree and VCF data into Apache Parquet format and annotate them with variant
effects and genomic scores. The default configuration for the annotation is
located into GPF data instance. In the case of GPF startup data instance the
annotation configuration file is::

    data-hg19-startup/annotation.conf

The tool for converting VCF data into Apache Parquet file format is
``vcf2parquet``. To run it you need to specify the pedigree file and the VCF
file you are converting. Also you need to specify where the tool should store
the result files::

    cd data-hg19-startup/studies/quad/
    mkdir out
    vcf2parquet.py vcf quad.ped quad.vcf -o out/

After this command is finished the result data should be stored into ``out/``
directory::

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

The ``id`` of the study should be unique into the GPF data instance,
``name`` is a human readable name of the study that will be used to display
the study into GPF web UI.


Generate Variant Reports (optional) [TBD]
+++++++++++++++++++++++++++++++++++++++++

Generate Denovo Gene Sets (optional) [TBD]
++++++++++++++++++++++++++++++++++++++++++


Start GPF Web UI
++++++++++++++++
