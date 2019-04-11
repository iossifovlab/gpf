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

    sudo apt-get install git wget build-essential zlib1g-dev libsasl2-dev


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
will need a `data-hg19-startup` instance.

.. code-block:: bash

    wget -c https://iossifovlab.com/distribution/public/data-hg19-startup.tar.gz

This command will copy the necessary data into your working directory. To
use you need to untar it:

.. code-block:: bash

    tar zxvf data-hg19-startup.tar.gz

This command is going to create  directory `data-hg19-startup` that contains
preconfigured GPF data for HG19.


Get Genomic Scores Database (optional)
######################################

To annotate variants with genomic scores you will need a genomic scores
database or at least genomic scores you plan to use. You can find some
genomic scores for HG19 at
`https://iossifovlab.com/distribution/public/genomic-scores-hg19/`

Download and untar the genomic scores you want to use into a separate
directory. For example, if you want to use `gnomAD_exome` and `gnomAD_genome`
frequencies:

.. code:: bash

    mkdir genomic-scores-hg19
    cd genomic-scores-hg19
    wget -c https://iossifovlab.com/distribution/public/genomic-scores-hg19/gnomAD_exome-hg19.tar
    wget -c https://iossifovlab.com/distribution/public/genomic-scores-hg19/gnomAD_genome-hg19.tar
    tar xvf gnomAD_exome-hg19.tar
    tar xvf gnomAD_genome-hg19.tar

This will create two subdirectories inside your `genomic-scores-hg19`
directory,
that contain `gnomAD_exome` and `gnomAD_genome` frequencies prepared to be used
by GPF annotation pipeline and GPF import tools.

.. note::

    If you want to use some genomic scores you should edit GPF annotation
    pipeline configuration file::

        data-hg19-startup/annotation.conf
    
    This configuration pipeline contains some examples how to configure
    genomic scores annotation for `MPC` and `CADD` genomic scores and
    for `gnomAD_exome` and `gnomAD_genome` frequencies. Comment out
    the appropriate example and adjust it according to your needs.


Update `setenv.sh` Script
#########################

Inside the GPF source directory, there is a file named
``setenv_template.sh``:

.. code-block:: bash

    # specifies where Apache Spark is installed
    export SPARK_HOME=<path to spark distribution>/spark-2.4

    # configure paths to genomic scores databases
    # export DAE_GENOMIC_SCORES_HG19=<path to>/genomic-scores-hg19
    # export DAE_GENOMIC_SCORES_HG38=<path to>/genomic-scores-hg38

    # specifies where the source directory for GPF DAE is
    export DAE_SOURCE_DIR=<path to gpf>/gpf/DAE
    # specifies the location of the GPF data instance
    export DAE_DB_DIR=<path to work data>/data-hg19

    # activates GPF conda environment
    conda activate gpf3

    # setups GPF paths
    source $DAE_SOURCE_DIR/setdae.sh


You should copy it as a separate file named ``setenv.sh`` and edit it according
you own setup.

.. note::

    If you plan to use genomic scores annotation you need to comment out
    setting of `DAE_GENOMIC_SCORES_HG19` and `DAE_GENOMIC_SCORES_HG38`
    environment variables and edit them accordingly.


When you are ready, you need to source your ``setenv.sh`` file:

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

In the GPF startup data instance there are some demo studies already
imported and configured:

    * `quad` with a couple of variants in a single quad family
    * `multi` with a couple of variants in a multigenerational family
    * ...

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

`simple_study_import.py` tool
*****************************

This tool supports variants import from two input formats:

* VCF format

* DAE de Novo list of variants

To see the available options supported by this tools use::

    simple_study_import.py --help

that will output short help message::

    usage: simple_study_import.py [-h] [--id <study ID>] [--vcf <VCF filename>]
                                [--denovo <de Novo variants filename>]
                                [-o <output directory>]
                                <pedigree filename>

    simple import of new study data

    positional arguments:
    <pedigree filename>   families file in pedigree format

    optional arguments:
    -h, --help            show this help message and exit
    --id <study ID>       unique study ID to use
    --vcf <VCF filename>  VCF file to import
    --denovo <de Novo variants filename>
                            DAE denovo variants file
    -o <output directory>, --out <output directory>
                            output directory. If none specified, "data/" directory
                            is used [default: data/]



Example import of VCF variants
******************************

Let say you have pedigree file `comp.ped` describing family information,
a VCF file `comp.vcf` with transmitted variants and a list of de Novo variants
`comp.tsv`. This example data could be found inside `$DAE_DB_DIR/studies/comp`
of the GPF startup data instance `data-hg19-startup`.

To import this data as a study into GPF instance:

* go into `studies` directory of GPF instance data folder::

    cd $DAE_DB_DIR/studies/comp


* run `simple_study_import.py` to import the data; this tool expects there
  arguments - study ID to use, pedigree file name and VCF file name::

        simple_study_import.py comp.ped --denovo comp.tsv --vcf comp.vcf



Generate Variant Reports (optional)
+++++++++++++++++++++++++++++++++++

To generate families and de Novo variants report, you should use
`generate_common_report.py`. This tool supports the option `--show-studies` to
list all studies and datasets configured in the GPF instance::

    generate_common_report.py --show-studies

To generate the families and variants reports for a given configured study
or dataset, you
should use `--studies` option. For example, to generate the families and
variants reports for the `quad` study, you should use::

    generate_common_report.py --studies comp


Generate Denovo Gene Sets (optional)
++++++++++++++++++++++++++++++++++++

To generate de Novo Gene sets, you should use the
`generate_denovo_gene_sets.py` tool. This tool supports the option
`--show-studies` to list all studies and datasets configured in the
GPF instance::

    generate_denovo_gene_sets.py --show-studies

To generate the de Novo gene sets for a given configured study
or dataset, you
should use `--studies` option. For example, to generate the de Novo
gene sets for the `quad` study, you should use::

    generate_denovo_gene_sets.py --studies comp


Start GPF Web UI
++++++++++++++++

After importing a new study into the GPF data instance, you need to restart the
GPF web UI. Stop the Django develompent server and start it again::

        ./manage.py runserver 0.0.0.0:8000


Work with Phenotype Data
########################

Simple Pheno Import Tool
++++++++++++++++++++++++

In the GPF startup data instance there is a demo phenotype database inside
the following directory::

    cd data-hg19-startup/pheno

The included files are:

* `pheno.ped` - the pedigree file for all families included into the database;

* `instruments` - directory, containing all instruments;

* `instruments/i1.csv` - all measurements for instrument `i1`.

* `comp_pheno_data_dictionary.tsv` - descriptions for all measurements

The easiest way to import this phenotype database into the GPF instance is to
use `simple_pheno_import.py` tool. This tool combines converting phenotype
instruments and measures into GPF phenotype database and generates data and
figures need for GPF Phonotype Browser. It will import the phenotype database
directly to the DAE data directory specified in your environment.

.. code::

    simple_pheno_import.py -p comp_pheno.ped \
        -i instruments/ -d comp_pheno_data_dictionary.tsv -o comp_pheno \
        --age "i1:age" --nonverbal_iq "i1:iq"

Options used in this command are as follows:

* `-p` option allows to specify the pedigree file;

* `-d` option specifies the name of the data dictionary file for the phenotype database

* | `-i` option allows to spcecify the directory where instruments
  | are located;

* | `-o` options specifies the name of the output phenotype database that will be
  | used in phenotype browser;

* | `--age` and `--nonverbal_iq` option specifies which measures ids
  | correspond to the age at assesment and non-verbal IQ; when such
  | measures are specified, the phenotype browser displays correlation
  | between each measure displayed and age at assesment and non-verbal IQ.

You can use `-h` option to see all options supported by the
`simple_pheno_import.py` tool.

Configure Phenotype Database
++++++++++++++++++++++++++++

The newly imported phenotype database has an automatically generated
configuration file.

.. code::

    [phenoDB]
    dbfile = comp_pheno.db
    age = age
    nonverbal_iq = iq
    browser_dbfile = browser/comp_pheno_browser.db
    browser_images_dir = browser/comp_pheno
    browser_images_url = /static/comp_pheno

Configure Phenotype Browser
+++++++++++++++++++++++++++

The phenotype databases could be attached to one or more studies and datasets.
If you want to attach `comp_pheno` phenotype database to `comp` study you need
to specify it in the `comp` stydy configuration file `comp.conf`:

.. code::

    [study]

    id = comp
    prefix = data/
    phenoDB = comp_pheno

and to enable the phenotype browser you should add:

.. code::

    phenotypeBrowser = yes

If you restart the GPF system WEB interface after this change you should be
able to see `Phenotype Browser` tab in `comp` dataset.

Configure Phenotype Filters in Genotype Browser
+++++++++++++++++++++++++++++++++++++++++++++++

A study or a dataset can have Phenotype Filters configured for it's Genotype
Browser when it has a phenoDB attached to it. The configuration looks like this:

.. code::

    [genotypeBrowser]

    phenoFilters.filters = continuous

    phenoFilters.continuous.name = Continuous
    phenoFilters.continuous.type = continuous
    phenoFilters.continuous.filter = multi:prb

`phenoFilters.filters` is a comma separated list of ids of the defined
Phenotype Filters. Each phenotype filter is expected to have a
`phenoFilters.<pheno_filter_id>` configuration.

The required configuration options for each pheno filter are:

* | `phenoFilters.<pheno_filter_id>.name` - name to use when showing the pheno
  | filter in the Genotype Browser Table Preview.

* | `phenoFilters.<pheno_filter_id>.type` - the type of the pheno filter. One
  | of `continuous`, `categorical`, `ordinal` or `raw`.

* `phenoFilters.<pheno_filter_id>.filter` - the definition of the filter.

The definition of a pheno filter has the format
`<filter_type>:<role>(:<measure_id>)`. Each of these

* | `filter_type` - either `single` or `multiple`. A single filter is used to
  | filter on only one specified measure (specified by `<measure_id>`). A
  | `multiple` pheno filter allows the user to choose which measure to use for
  | filtering. The available measures depend on the
  | `phenoFilters.<pheno_filter_id>.type` field.

* | `role` - which persons' phenotype data to use for this filter. Ex. `prb`
  | uses the probands' values for filtering. When the role matches more than
  | one person the first is chosen.

* | `measure_id` - id of the measure to be used for a `single` filter. Not
  | used when a `multiple` filter is being defined.

After adding the configuration for Phenotype Filters and reloading the Genotype
Browser the Advanced option of the Family Filters should be present.

Configure Phenotype Columns in Genotype Browser
+++++++++++++++++++++++++++++++++++++++++++++++

Phenotype Columns are values from the Phenotype Database for each variant
displayed in Genotype Browser Preview table. They can be added when a phenoDB
is attached to a study or a dataset.

To add a Phenotype Column you need to define it in the study or dataset config:

.. code::

    [genotypeBrowser]

    pheno.columns = pheno

    pheno.pheno.name = Measures
    pheno.pheno.slots = prb:i1.age:Age,
        prb:i1.iq:Iq


The `pheno.columns` property is a comma separated list of ids for each Pheno
Column. Each Pheno Column has to have a `pheno.<measure_id>` configuration with
the following properties:

* | `pheno.<measure_id>.name` - the display name of the pheno column group used
  | in the Genotype Browser Preview table.

* | `pheno.<measure_id>.slots` - comma separated definitions for all pheno
  | columns.

The Phenotype Column definition has the following structure:
`<role>:<measure_id>:<name>`, where:

* | `<role>` - role of the person whose pheno values will be displayed. If
  | the role matches two or more people all of their values will be shown,
  | separated with a comma.

* `<measure_id>` - id of the measure whose values will be displayed.

* `<name>` - the name of the sub-column to be displayed.

For the Phenotype Columns to be in the Genotype Browser Preview table or the
Genotype Browser Download file, they have to be present in the `previewColumns`
or the `downloadColumns` in the Genotype Browser configuration.

.. code::

    previewColumns = family,variant,genotype,effect,weights,
    scores3,scores5,
    pheno


In the above `comp` configuration the last column `pheno` is a Phenotype Column.

Phenotype Database Tools
++++++++++++++++++++++++

Import a Demo Phenotype Dabase
******************************

In the GPF startup data instance there is a demo phenotype database inside
the following directory::

    cd data-hg19-startup/pheno

The included files are:

* `pheno.ped` - the pedigree file for all families included into the database;

* `instruments` - directory, containing all instruments;

* `instruments/i1.csv` - all measurements for instrument `i1`.

To import these phenotype database into the GPF system you need to use
`pheno2DAE.py` tool::

    pheno2dae.py -p comp_pheno.ped -i instruments/ -d comp_pheno_data_dictionary.tsv -o comp_pheno.db

Options uses in this command are as follows:

* `-p` option allows us to specify the pedigree file;

* | `-i` option allows us to spcecify the directory where instruments
  | are located;

* `-d` option specifies the name of the data dictionary file for the phenotype database

* `-o` options specifies the name of the output file.

You can use `-h` option to see all options supported by the `pheno2dae.py`
tool.

Generate Pheno Browser Data
***************************

To generate the data needed for the GPF Phenotype Browser you can use
`pheno2browser.py` tool. Example usege of the tools is shown bellow:

.. code:: bash

    pheno2browser.py -d ./comp_pheno.db -p comp_pheno \
        -o browser/comp_pheno \
        --age "i1:age" --nonverbal_iq "i1:iq"

Options used in this example are as follows:

* `-d` option specifies path to already imported phenotype database file;

* | `-p` options specifies the name of the phenotype database that will be
  | used in phenotype browser;

* | `-o` option specifies the output directory where all the generated
  | file will be stored;

* | `--age` and `--nonverbal_iq` option specifies which measures ids
  | correspond to the age at assesment and non-verbal IQ; when such
  | measures are specified, the phenotype browser displays correlation
  | between each measure displayed and age at assesment and non-verbal IQ.
