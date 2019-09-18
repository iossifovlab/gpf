GPF Getting Started Guide
=========================


Prerequisites [WIP]
###################

.. note::
    wget

If you are using Ubuntu, you can run:

.. code-block:: bash

    sudo apt-get install wget


GPF Installation
################

The GPF system is developed in Python and supports Python 3.6 and up. The
recommended way to setup the GPF development environment is to use Anaconda.

Download and install Anaconda
+++++++++++++++++++++++++++++

Download Anaconda from the Anaconda distribution page
(https://www.anaconda.com/distribution/):

.. code-block:: bash

    wget -c https://repo.anaconda.com/archive/Anaconda3-2019.07-Linux-x86_64.sh

and install it in your local environment, following the installer instructions:

.. code-block:: bash

    sh Anaconda3-2019.07-Linux-x86_64.sh


.. note::

    At the end of the installation process, you will be asked if you wish
    to allow the installer to initialize Anaconda3 by running conda init.
    If you choose to, every terminal you open after that will have the ``base``
    Anaconda environment activated, and you'll have access to the ``conda`` commands
    used below.

Install GPF
+++++++++++

Create an empty conda `gpf` environment:

.. code-block:: bash

    conda create -n gpf

To use this environment, you need to activate it using the following command:

.. code-block:: bash

    conda activate gpf

Install the `gpf_wdae` conda package into the already activated `gpf`
environment:

.. code-block:: bash

    conda install -c conda-forge -c bioconda -c iossifovlab gpf_wdae

This command is going to install GPF and all its dependencies.


Bootstrap GPF
+++++++++++++

To start working with GPF, you will need a startup data instance. There are
two GPF startup instances that are aligned with different versions of the
reference human genome - for HG19 and HG38.

Besides the startup data instance some initial bootstrapping of GPF is also
necessary.

To make bootstrapping easier, the script ``wdae_bootstrap.sh`` is provided,
which prepares GPF for initial start.

The bootstrap script creates a working directory where the data will be
stored. You can provide the name of the working directory as a parameter
to the boostrap script. For example, if you want the working directory to
be named `gpf_test`, use the following command:


    * For HG19:
        .. code-block:: bash

            wdae_bootstrap.sh hg19 gpf_test

    * For HG38
        .. code-block:: bash

            wdae_bootstrap.sh hg38 gpf_test

As a result, a directory named `gpf_test` should be created with following
structure:

.. code-block:: bash

    gpf_test
    ├── annotation.conf
    ├── DAE.conf
    ├── defaultConfiguration.conf
    ├── geneInfo
    ├── geneInfo.conf
    ├── genomes
    ├── genomesDB.conf
    ├── genomicScores
    ├── genomicScores.conf
    ├── genomic-scores-hg19
    ├── genomic-scores-hg38
    ├── pheno
    ├── studies
    └── wdae


Run GPF web server
##################

Enter into ``gpf_test/wdae`` and source ``setenv.sh`` file:

.. code-block:: bash

    cd gpf_test/wdae
    source ./setenv.sh

You are now ready to run the GPF development web server:

.. code-block:: bash

    wdaemanage.py runserver 0.0.0.0:8000

You can browse the development server using the IP of the host you're running
the server on at port 8000. For example, if you are running the GPF
develompent server locally, you can use the following URL:

.. code-block:: bash

    http://localhost:8000


Import a Demo Dataset
#####################

In the GPF startup data instance there are some demo studies already
imported and configured:

    * `comp` with a couple of variant in a complex family
    * `multi` with a couple of variants in a multigenerational family

.. note::
    You can download some more publicly available studies, which are prepared to be
    included into the GPF startup data instance.

To demonstrate how to import new study data into the GPF data instance, we
will reproduce the necessary steps for importing the `comp` study data.

Start or Configure Apache Impala
++++++++++++++++++++++++++++++++

.. note::
   Docker can be installed by following the instructions at
   https://docs.docker.com/install/linux/docker-ce/ubuntu/.

By default GPF uses Apache Impala as a backend for storing genomic variants.
The GPF import tools import studies data into Impala. To make using GPF
easier, we provide a Docker container with Apache Impala. To run it, you
can use::

    docker run \
        --name gpf_impala \
        --hostname impala \
        -p 8020:8020 \
        -p 9870:9870 \
        -p 9864:9864 \
        -p 21050:21050 \
        -p 25000:25000 \
        -p 25010:25010 \
        -p 25020:25020 \
        seqpipe/seqpipe-docker-impala:latest

This command creates and starts Docker container named `gpf_impala`
containing all the components needed for running Apache Impala.

.. note::
    The option `-p` (`--port`) used in `docker run` command instructs the
    Docker to make specified port accessible from the host environment. For
    example `-p 8020:8020` makes port 8020 from docker container `gpf_impala`
    accessible from `localhost`. The ports specified in this command are:

        - 8020 - port for accessing HDFS
        - 9870 - port for Web interface to HDFS Named Node (optional)
        - 9864 - port for Web interface to HDFS Data Node (optional)
        - 21050 - port for accessing Impala
        - 25000 - port for Web interface to Impala deamon  (optional)
        - 25010 - port for Web interface to Impala state store  (optional)
        - 25020 - port for Web interface to Impala catalog  (optional)

.. note::
    In case you need to stop and start this container multiple times you can
    use Docker comands `docker stop gpf_impala` and `docker start gpf_impala`.


Simple study import
+++++++++++++++++++

Importing study data into a GPF instance usually involves multiple steps. To
make initial bootstraping easier you can use the ``simple_study_import.py``
tool that combines all the necessary steps in one tool.

`simple_study_import.py` tool
*****************************

This tool supports variants import from two input formats:

* VCF format

* DAE de Novo list of variants

To see the available options supported by this tools use::

    simple_study_import.py --help

which will output a short help message::

    usage: simple_study_import.py [-h] [--id <study ID>] [--vcf <VCF filename>]
                                [--denovo <de Novo variants filename>]
                                [-o <output directory>] [--skip-reports]
                                <pedigree filename>

    simple import of new study data

    positional arguments:
    <pedigree filename>   families file in pedigree format

    optional arguments:
    -h, --help            show this help message and exit
    --id <study ID>       Unique study ID to use. If not specified the basename
                            of the family pedigree file is used for study ID
    --vcf <VCF filename>  VCF file to import
    --denovo <de Novo variants filename>
                            DAE denovo variants file
    -o <output directory>, --out <output directory>
                            output directory for storing intermediate parquet
                            files. If none specified, "parquet/" directory inside
                            GPF instance study directory is used [default: None]
    --skip-reports        skip running report generation [default: False]


Example import of variants
**************************

Let's say you have a pedigree file ``comp.ped`` describing family information,
a VCF file ``comp.vcf`` with transmitted variants and a list of de Novo
variants ``comp.tsv``. This example data can be found inside
``$DAE_DB_DIR/studies/comp`` of the GPF startup data instance `gpf_test`.

To import this data as a study into the GPF instance:

* go into `studies` directory of the GPF instance data folder::

    cd $DAE_DB_DIR/studies/comp


* run ``simple_study_import.py`` to import the VCF variants; this command uses
  three arguments - study ID to use, pedigree file name and VCF file name::

        simple_study_import.py --id comp_vcf \
            --vcf comp.vcf \
            comp.ped

  This command creates a study with ID `comp_vcf` that contains all VCF
  variants.


* run ``simple_study_import.py`` to import the de Novo variants; this command
  uses three arguments - study ID to use, pedigree file name and VCF file
  name::

        simple_study_import.py --id comp_denovo \
            --denovo comp.tsv \
            comp.ped

  This command creates a study with ID `comp_denovo` that contains all de
  Novo variants.

* run ``simple_study_import.py`` to import all VCF and de Novo variants;
  this command uses four arguments - study ID to use, pedigree file name,
  VCF file name and de Novo variants file name::

        simple_study_import.py --id comp_all \
            --denovo comp.tsv \
            --vcf comp.vcf \
            comp.ped

  This command creates a study with ID `comp_all` that contains all
  VCF and de Novo variants.


.. note::
    The expected format for the de Novo variants file is a tab separated
    file that contains following columns:

    - familyId - family Id matching a family from the pedigree file
    - location - location of the variant
    - variant - description of the variant
    - bestState - best state of the variant in the family

    Example::

        familyId       location       variant        bestState
        f1             1:865664       sub(G->A)      2 2 1 2/0 0 1 0
        f1             1:865691       sub(C->T)      2 2 1 2/0 0 1 0
        f2             1:865664       sub(G->A)      2 2 1 2/0 0 1 0
        f2             1:865691       sub(C->T)      2 2 1 2/0 0 1 0



Example import of de Novo variants
**********************************

As an example of importing study with de Novo variants you can use data
from::

    wget -c https://iossifovlab.com/distribution/public/studies/iossifov_2014-latest.tar.gz

Untar this data::

    tar zxf iossifov_2014-latest.tar.gz

and run ``simple_study_import.py`` tool::

    cd iossifov_2014/
    simple_study_import.py --id iossifov_2014 \
        --denovo IossifovWE2014.tsv \
        IossifovWE2014.ped

To see the imported variants, restart the GPF development web server and find
`iossifov_2014` study.



Example Usage of GPF Python Interface
#####################################

Simplest way to start using GPF's Python API is to import the ``VariantsDb``
class and instantiate it with the default DAE configuration:

.. code-block:: python3

    from dae.DAE import dae_config
    from dae.studies.variants_db import VariantsDb
    vdb = VariantsDb(dae_config)

This ``vdb`` factory object allows you to get all studies and datasets in the
configured GPF instance. For example to list all studies configured in
the startup GPF instance use:

.. code-block:: python3

    vdb.get_studies_ids()

This should return a list of all studies' IDs:

.. code-block:: python3

    ['iossifov_2014',
    'iossifov_2014_small',
    'trio',
    'quad',
    'multi',
    'ivan']

To get a specific study and query it, you can use:

.. code-block:: python3

    st = vdb.get_study("trio")
    vs = st.query_variants()
    vs = list(vs)

.. note::
    The `query_variants` method returns a Python iterator.

To get the basic information about variants found by ``query_variants`` method,
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

The ``query_variants`` interface allows you to specify what kind of variants
you are interested in. For example, if you only need 'missense' variants, you
can use:

.. code-block:: python3

    st = vdb.get_study("iossifov_2014_small")
    vs = st.query_variants(effect_types=['missense'])
    vs = list(vs)
    print(len(vs))

    >> 6

Or, if you are interested in 'missense' variants only in people with role
'prb' you can use:

.. code-block:: python3

    vs = st.query_variants(effect_types=['missense'], roles='prb')
    vs = list(vs)
    len(vs)

    >> 3



Getting Started with Phenotype Data
###################################

Simple Pheno Import Tool
++++++++++++++++++++++++

In the directory produced by ``wdae_bootstrap.sh``, there is a
demo phenotype database inside the ``pheno`` directory::

    cd gpf_test/pheno

This phenotype database is ``comp_pheno``. It has already been imported into the
GPF instance, but its initial files have also been included in order to demonstrate
how a phenotype database may be imported.

The included files are:

* ``comp_pheno.ped`` - the pedigree file for all families included into the database;

* ``instruments`` - directory, containing all instruments;

* ``instruments/i1.csv`` - all measurements for instrument ``i1``.

* ``comp_pheno_data_dictionary.tsv`` - descriptions for all measurements

* ``comp_pheno_regressions.conf`` - regression configuration file

The easiest way to import this phenotype database into the GPF instance is to
use `simple_pheno_import.py` tool. This tool combines converting phenotype
instruments and measures into a GPF phenotype database and generates data and
figures needed for GPF Phenotype Browser. It will import the phenotype database
directly to the DAE data directory specified in your environment.

.. code::

    simple_pheno_import.py -p comp_pheno.ped \
        -i instruments/ -d comp_pheno_data_dictionary.tsv -o comp_pheno_manual_import \
        --regression comp_pheno_regressions.conf

Options used in this command are as follows:

* ``-p`` option allows to specify the pedigree file;

* | ``-d`` option specifies the name of the data dictionary file for the
  | phenotype database

* | ``-i`` option allows to specify the directory where instruments
  | are located;

* | ``-o`` options specifies the name of the output phenotype database that
  | will be used in phenotype browser;

* | ``--regression`` option specifies a path to a pheno regression config which
  | describes a list of measures to make regressions against

You can use ``-h`` option to see all options supported by the
``simple_pheno_import.py`` tool.

Configure Phenotype Database
++++++++++++++++++++++++++++

Phenotype databases have a short configuration file (whose filenames
usually end with the extension ``.conf``) which points
the system to their files, as well as specifying some
other properties. When importing a phenotype database through the
`simple_pheno_import.py` tool, a configuration file is automatically
generated. You may inspect the ``comp_pheno_manual_import`` directory
to see the configuration file generated from the import tool:

.. code::

    [phenoDB]
    name = comp_pheno_manual_import
    dbfile = %(wd)s/comp_pheno_manual_import.db
    browser_dbfile = %(wd)s/browser/comp_pheno_manual_import_browser.db
    browser_images_dir = %(wd)s/browser/comp_pheno_manual_import
    browser_images_url = /static/comp_pheno_manual_import

Configure Phenotype Browser
+++++++++++++++++++++++++++

To demonstrate how a study is configured with a phenotype database, we will
be working with the manually imported ``comp_all`` study.

The phenotype databases could be attached to one or more studies and datasets.
If you want to attach ``comp_pheno_manual_import`` phenotype
database to ``comp_all`` study, you need to specify it in the ``comp_all``
study configuration file ``comp_all.conf``:

.. code::

    [study]

    id = comp_all
    prefix = data/
    phenoDB = comp_pheno_manual_import

and to enable the phenotype browser you must add:

.. code::

    phenotypeBrowser = yes

If you restart the GPF system WEB interface after this change you should be
able to see `Phenotype Browser` tab in `comp_all` dataset.

Configure Phenotype Filters in Genotype Browser
+++++++++++++++++++++++++++++++++++++++++++++++

A study or a dataset can have Phenotype Filters configured for its Genotype
Browser when it has a phenoDB attached to it. The configuration looks like
this:

.. code::

    [genotypeBrowser]

    phenoFilters.filters = sampleContinuousFilter

    phenoFilters.sampleContinuousFilter.name = sampleFilterName
    phenoFilters.sampleContinuousFilter.type = continuous
    phenoFilters.sampleContinuousFilter.filter = multi:prb

``phenoFilters.filters`` is a comma separated list of ids of the defined
Phenotype Filters. Each phenotype filter is expected to have a
``phenoFilters.<pheno_filter_id>`` configuration.

The required configuration options for each pheno filter are:

* | ``phenoFilters.<pheno_filter_id>.name`` - name to use when showing the
  | pheno filter in the Genotype Browser Table Preview.

* | ``phenoFilters.<pheno_filter_id>.type`` - the type of the pheno filter. One
  | of ``continuous``, ``categorical``, ``ordinal`` or ``raw``.

* ``phenoFilters.<pheno_filter_id>.filter`` - the definition of the filter.

The definition of a pheno filter has the format
``<filter_type>:<role>(:<measure_id>)``. Each of these

* | ``filter_type`` - either ``single`` or ``multiple``. A single filter is
  | used to filter on only one specified measure (specified by
  | ``<measure_id>``). A ``multiple`` pheno filter allows the user to choose
  | which measure to use for filtering. The available measures depend on the
  | ``phenoFilters.<pheno_filter_id>.type`` field.

* | ``role`` - which persons' phenotype data to use for this filter. Ex.
  | ``prb`` uses the probands' values for filtering. When the role matches more
  | than one person the first is chosen.

* | ``measure_id`` - id of the measure to be used for a ``single`` filter. Not
  | used when a ``multiple`` filter is being defined.

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


The ``pheno.columns`` property is a comma separated list of ids for each Pheno
Column. Each Pheno Column has to have a ``pheno.<measure_id>`` configuration with
the following properties:

* | ``pheno.<measure_id>.name`` - the display name of the pheno column group
  | used in the Genotype Browser Preview table.

* | ``pheno.<measure_id>.slots`` - comma separated definitions for all pheno
  | columns.

The Phenotype Column definition has the following structure:
``<role>:<measure_id>:<name>``, where:

* | ``<role>`` - role of the person whose pheno values will be displayed. If
  | the role matches two or more people all of their values will be shown,
  | separated with a comma.

* ``<measure_id>`` - id of the measure whose values will be displayed.

* ``<name>`` - the name of the sub-column to be displayed.

For the Phenotype Columns to be in the Genotype Browser Preview table or the
Genotype Browser Download file, they have to be present in the
``previewColumns`` or the ``downloadColumns`` in the Genotype Browser
configuration.

.. code::

    previewColumns = family,variant,genotype,effect,weights,scores3,scores5,pheno


In the above ``comp_all`` configuration, the last column ``pheno`` is a Phenotype
Column.


Enabling the Phenotype tool
+++++++++++++++++++++++++++

To enable the Phenotype tool for a study, you must edit
its configuration file and set the appropriate property, as with
the Phenotype browser. Open the configuration file ``comp_all.conf``:

.. code::

    [study]

    id = comp
    prefix = data/
    phenoDB = comp_pheno
    phenotypeBrowser = yes
    genotypeBrowser = yes


You can enable the Phenotype tool using the following property:

.. code::

   phenotypeTool = yes


Restart the GPF development web server and select the `comp_all` study.
You should see a :ref:`phenotool-ui` tab. Once you have selected it, you can select
a phenotype measure of your choice. To get the tool to acknowledge the variants
in the ``comp_all`` study, select the `All` option of the `Present in Parent` field.
Since the effect types of the variants in the comp study are only `Missense` and `Synonymous`,
you may wish to de-select the `LGDs` option under the `Effect Types` field.
There are is also the option to normalize the results by one or two measures
configured as regressors - age and non-verbal IQ.

Click on the `Report` button to produce the results.


Dataset Statitistics and de Novo Gene Sets
##########################################

Generate Variant Reports (optional)
+++++++++++++++++++++++++++++++++++

To generate families and de Novo variants report, you should use
``generate_common_report.py``. This tool supports the option ``--show-studies``
to list all studies and datasets configured in the GPF instance::

    generate_common_report.py --show-studies

To generate the families and variants reports for a given configured study
or dataset, you can use the ``--studies`` option.
For example, to generate the families and
variants reports for the `quad` study, you should use::

    generate_common_report.py --studies comp


Generate Denovo Gene Sets (optional)
++++++++++++++++++++++++++++++++++++

To generate de Novo Gene sets, you should use the
``generate_denovo_gene_sets.py`` tool. This tool supports the option
``--show-studies`` to list all studies and datasets configured in the
GPF instance::

    generate_denovo_gene_sets.py --show-studies

To generate the de Novo gene sets for a given configured study
or dataset, you can use ``--studies`` option.
For example, to generate the de Novo
gene sets for the `quad` study, you should use::

    generate_denovo_gene_sets.py --studies comp


Getting Started with Annotation Pipeline
########################################


Get Genomic Scores Database (optional)
++++++++++++++++++++++++++++++++++++++

To annotate variants with genomic scores you will need a genomic scores
database or at least genomic scores you plan to use. You can find some
genomic scores for HG19 at:

https://iossifovlab.com/distribution/public/genomic-scores-hg19/

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
directory, that contain `gnomAD_exome` and `gnomAD_genome`
frequencies prepared to be used by GPF annotation pipeline and GPF import tools.

Annotation configuration
++++++++++++++++++++++++

If you want to use some genomic scores, you must edit the GPF annotation
pipeline configuration file:

.. code::

    gpf_test/annotation.conf

This configuration pipeline contains some examples on how to configure
annotation with `MPC` and `CADD` genomic scores and
for `gnomAD exome` and `gnomAD genome` frequencies. Comment out
the appropriate example and adjust it according to your needs.

The genomic scores folders inside the directory generated by
``wdae_bootstrap.sh`` - ``genomic-scores-hg19`` and ``genomic-scores-hg38`` are
the default locations where the annotation pipeline will resolve the
interpolation strings ``%(GENOMIC_SCORES_HG19)s`` and
``%(GENOMIC_SCORES_HG38)s``, respectively. These interpolation strings are used
when specifying the location of the genomic score to use
(e.g. ``%(GENOMIC_SCORES_HG19)s/CADD/CADD.bedgraph.gz``).

You can put your genomic scores inside these directories, or you can specify a
custom ``GENOMIC_SCORES_HG19`` path at the top of the annotation configuration
file. Beware that this will likely break genomic scores which were specified
using the old path.
