GPF Getting Started Guide
=========================


Prerequisites
#############

This guide assumes that you are working on a Linux distribution.

You need wget to follow this guide - you can use your system's package manager to install it. For example, on Ubuntu:

.. code-block:: bash

    sudo apt-get install wget


GPF Installation
################

The GPF system is developed in Python and supports Python 3.7 and up. The
recommended way to setup the GPF development environment is to use Anaconda.

Download and install Anaconda
+++++++++++++++++++++++++++++

Download Anaconda from Anaconda's `distribution page <https://www.anaconda.com/distribution>`_ using the following command:

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

Create an empty Anaconda environment named `gpf`:

.. code-block:: bash

    conda create -n gpf

To use this environment, you need to activate it using the following command:

.. code-block:: bash

    conda activate gpf

Install the `gpf_wdae` conda package into the already activated `gpf`
environment:

.. code-block:: bash

    conda install -c defaults -c conda-forge -c iossifovlab -c bioconda gpf_wdae

This command is going to install GPF and all of its dependencies.


Bootstrap GPF
+++++++++++++

To start working with GPF, you will need a startup data instance. There are
two GPF startup instances that are aligned with different versions of the
reference human genome - for HG19 and HG38.

Besides the startup data instance, some initial bootstrapping of GPF is also
necessary.

The bootstrap script ``wdae_bootstrap.sh`` creates a working directory where the data will be
stored. You can provide the name of the working directory as a parameter
to the boostrap script. For example, if you want the working directory to
be named `gpf_test`, use the following command:


* For HG19:
    .. code-block:: bash

        wdae_bootstrap.sh hg19 gpf_test

* For HG38
    .. code-block:: bash

        wdae_bootstrap.sh hg38 gpf_test

As a result, a directory named `gpf_test` will be created with the following
structure:

.. code-block:: bash

    gpf_test
    ├── annotation.conf
    ├── DAE.conf
    ├── datasets
    ├── datasetsDB.conf
    ├── defaultConfiguration.conf
    ├── enrichment
    ├── geneInfo
    ├── geneInfo.conf
    ├── genomes
    ├── genomesDB.conf
    ├── genomicScores
    ├── genomicScores.conf
    ├── genomic-scores-hg19
    ├── genomic-scores-hg38
    ├── permissionDeniedPrompt.md
    ├── pheno
    ├── setenv.sh
    ├── studies
    ├── studiesDB.conf
    └── wdae


Run GPF web server
##################

Enter into the newly created ``gpf_test`` directory and source the ``setenv.sh`` file:

.. code-block:: bash

    cd gpf_test
    source ./setenv.sh

To run the GPF development web server, use the ``wdaemanage.py``
command provided by the conda environment. To do so, run:

.. code-block:: bash

    wdaemanage.py runserver 0.0.0.0:8000

You can browse the development server using the IP address and port
provided to the wdaemanage.py command. In this case:

.. code-block:: bash

    http://localhost:8000

Once loaded, you will be greeted by a blank page. To demonstrate how to import new study data into
the GPF instance, we will reproduce the necessary steps for importing a sample study.

Data Storage
++++++++++++

By default, GPF uses the filesystem for storing imported genotype data.
This is fine for smaller sized studies, however, there is an option to use
Apache Impala as storage. This can be especially useful for larger studies.
If you wish to use Apache Impala as storage, refer to :ref:`impala_storage`.

Simple study import
+++++++++++++++++++

Importing study data into a GPF instance involves multiple steps. To
make initial bootstraping easier, you can use the ``simple_study_import.py``
tool which combines all the necessary steps in one tool.

`simple_study_import.py` tool
*****************************

This tool supports importing variants from three formats:

* Variant Call Format (VCF)

* CSHL transmitted variants format

* :ref:`List of de Novo variants <denovo_format>`

To see the available options supported by this tool use::

    simple_study_import.py --help


Example import of variants
**************************

.. warning::
    Make sure not to extract the downloaded study in the gpf_test/studies folder,
    as this is where the system imports and reads its data to/from.

* Download the sample study and extract it::

    wget -c https://iossifovlab.com/distribution/public/studies/genotype-comp-latest.tar.gz
    tar zxvf genotype-comp-latest.tar.gz

It contains a pedigree file ``comp.ped`` with family information,
a VCF file ``comp.vcf`` with transmitted variants and a list of de Novo
variants ``comp.tsv``.


* Enter into the created directory ``comp``::

    cd comp

* Run ``simple_study_import.py`` to import the VCF variants; this command uses
  three arguments - pedigree file name, a VCF file name and an id to assign to the imported study in the system::

        simple_study_import.py comp.ped \
            --vcf-files comp.vcf \
            --id comp_vcf

  | This command creates a study with ID `comp_vcf` that contains all VCF variants.

* Run ``simple_study_import.py`` to import the de Novo variants; this command
  uses three arguments - study ID to use, pedigree file name and de Novo variants file name::

        simple_study_import.py comp.ped \
            --denovo-file comp.tsv \
            --id comp_denovo

  | This command creates a study with ID `comp_denovo` that contains all de Novo variants.

* Run ``simple_study_import.py`` to import all VCF and de Novo variants;
  this command uses four arguments - study ID to use, pedigree file name,
  VCF file name and de Novo variants file name::

        simple_study_import.py comp.ped \
            --denovo-file comp.tsv \
            --vcf-files comp.vcf \
            --id comp_all

  This command creates a study with ID `comp_all` that contains all
  VCF and de Novo variants.

.. _denovo_format:

.. note::
    The expected format for the de Novo variants file is a tab-separated
    file that contains the following columns:

    - familyId - family id matching a family from the pedigree file
    - location - location of the variant
    - variant - description of the variant
    - bestState - best state of the variant in the family

    The columns of your file may have different labels - if so, the
    simple_study_import tool accepts arguments which specify the labels
    of the columns in the input file.

    Example::

        familyId       location       variant        bestState
        f1             1:865664       sub(G->A)      2 2 1 2/0 0 1 0
        f1             1:865691       sub(C->T)      2 2 1 2/0 0 1 0
        f2             1:865664       sub(G->A)      2 2 1 2/0 0 1 0
        f2             1:865691       sub(C->T)      2 2 1 2/0 0 1 0



Example import of de Novo variants
**********************************

As an example of importing a study with de Novo variants, you can use the `iossifov_2014` study.
Download and extract the study::

    wget -c https://iossifovlab.com/distribution/public/studies/genotype-iossifov_2014-latest.tar.gz
    tar zxf genotype-iossifov_2014-latest.tar.gz

Enter into the created directory ``iossifov_2014``::

    cd iossifov_2014

and run the ``simple_study_import.py`` tool::

    simple_study_import.py IossifovWE2014.ped \
        --id iossifov_2014 \
        --denovo-file IossifovWE2014.tsv

To see the imported variants, restart the GPF development web server and navigate to the
`iossifov_2014` study.


Getting Started with Enrichment Tool
####################################

For studies that include de Novo variants, you can enable the :ref:`enrichment_tool_ui`.
As an example, let us enable it for the already imported
`iossifov_2014` study.

Go to the directory where the configuration file of the `iossifov_2014`
study is located::

    cd gpf_test/studies/iossifov_2014

Edit the study configuration file ``iossifov_2014.conf`` and add the following section in the end of the file::

    [enrichment]
    enabled = true

Restart the GPF web server::

    wdaemanage.py runserver 0.0.0.0:8000

Now when you navigate to the iossifov_2014 study in the browser,
the Enrichment Tool tab will be available.

Getting Started with Preview Columns
####################################

For each study you can specify which columns are shown in the variants' table preview, as well as those which will be downloaded.

As an example we are going to redefine the `Frequency` column in the `comp_vcf`
study imported in the previous example.

Navigate to the `comp_vcf` study folder:

.. code::

    cd gpf_test/studies/comp_vcf


Edit the "genotype_browser" section in the configuration file ``comp_vcf.conf`` to looks like this:

.. code::

    [genotype_browser]
    enabled = true
    genotype.freq.name = "Frequency"
    genotype.freq.slots = [
        {source = "exome_gnomad_af_percent", name = "exome gnomad", format = "E %%.3f"},
        {source = "genome_gnomad_af_percent", name = "genome gnomad", format = "G %%.3f"},
        {source = "af_allele_freq", name = "study freq", format = "S %%.3f"}
    ]

This overwrites the definition of the default preview column `Frequency` to
include not only the gnomAD frequencies, but also the allele frequencies.


Getting Started with Phenotype Data
###################################

Simple Pheno Import Tool
++++++++++++++++++++++++

The GPF simple pheno import tool prepares phenotype data to be used by the GPF
system.

As an example, we are going to show how to import simulated phenotype 
data into our GPF instance.

Download the archive and extract it outside of the GPF instance data directory:

.. code::

    wget -c https://iossifovlab.com/distribution/public/pheno/phenotype-comp-data-latest.tar.gz
    tar zxvf phenotype-comp-data-latest.tar.gz

Navigate to the newly created ``comp-data`` directory::

    cd comp-data

Inside you can find the following files:

* ``comp_pheno.ped`` - the pedigree file for all families included into the database

* ``instruments`` - directory, containing all instruments

* ``instruments/i1.csv`` - all measurements for instrument ``i1``

* ``comp_pheno_data_dictionary.tsv`` - descriptions for all measurements

* ``comp_pheno_regressions.conf`` - regression configuration file

To import the phenotype data, you can use the ``simple_pheno_import.py`` tool. It will import
the phenotype database directly to the DAE data directory specified in your environment:

.. code::

    simple_pheno_import.py \
        -p comp_pheno.ped \
        -d comp_pheno_data_dictionary.tsv \
        -i instruments/ \
        -o comp_pheno \
        --regression comp_pheno_regressions.conf

Options used in this command are as follows:

* ``-p`` specifies the pedigree file

* ``-d`` specifies the name of the data dictionary file for the phenotype database

* ``-i`` specifies the directory where the instruments are located

* ``-o`` specifies the name of the output phenotype database that will be used in the Phenotype Browser

* ``--regression`` specifies the path to the pheno regression config, describing a list of measures to make regressions against

You can use the ``-h`` option to see all options supported by the tool.

Configure Phenotype Database
++++++++++++++++++++++++++++

Phenotype databases have a short configuration file which points
the system to their files, as well as specifying additional properties.
When importing a phenotype database through the
``simple_pheno_import.py`` tool, a configuration file is automatically
generated. You may inspect the ``gpf_test/pheno/comp_pheno/comp_pheno.conf``
configuration file generated from the import tool:

.. code::

    [vars]
    wd = "."

    [phenotype_data]
    name = "comp_pheno"
    dbfile = "%(wd)s/comp_pheno.db"
    browser_dbfile = "%(wd)s/browser/comp_pheno_browser.db"
    browser_images_dir = "%(wd)s/browser/images"
    browser_images_url = "/static/comp_pheno/browser/images/"

    [regression.age]
    instrument_name = "i1"
    measure_name = "age"
    display_name = "Age"
    jitter = 0.1

    [regression.iq]
    instrument_name = "i1"
    measure_name = "iq"
    display_name = "Non verbal IQ"
    jitter = 0.1

Configure Phenotype Browser
+++++++++++++++++++++++++++

To demonstrate how a study is configured with a phenotype database, we will
be working with the already imported ``comp_all`` study.

The phenotype databases can be attached to one or more studies and/or datasets.
If you want to attach the ``comp_pheno`` phenotype
database to the ``comp_all`` study, you need to specify it in the study's
configuration file, which can be found at ``gpf_test/studies/comp_all/comp_all.conf``.

Add the following line at the beginning of the file, outside of any section:

.. code::

    phenotype_data = "comp_pheno"

To enable the :ref:`phenotype_browser_ui`, add this line:

.. code::

    phenotype_browser = true

After this, the configuration file should look like this:

.. code::

    id = "comp_all"
    conf_dir = "."
    has_denovo = true
    phenotype_browser = true
    phenotype_data = "comp_pheno"

    [genotype_storage]
    id = "genotype_filesystem"

    [genotype_storage.files]
    pedigree.path = "data/comp.ped"
    pedigree.params = {}

    [[genotype_storage.files.variants]]
    path = "data/comp.tsv"
    format = "denovo"
    params = {}

    [[genotype_storage.files.variants]]
    path = "data/comp.vcf"
    format = "vcf"
    params = {}

    [genotype_browser]
    enabled = true

When you restart the server, you should be
able to see the 'Phenotype Browser' tab in the `comp_all` study.

Configure Phenotype Filters in Genotype Browser
+++++++++++++++++++++++++++++++++++++++++++++++

A study or a dataset can have phenotype filters configured for its :ref:`genotype_browser_ui`
when it has a phenotype database attached to it. The configuration looks like this:

.. code::

    [genotype_browser]
    enabled = true
    selected_pheno_filters_values = ["sample_continuous_filter"]

    pheno_filters.sample_continuous_filter.name = "Sample Filter Name"
    pheno_filters.sample_continuous_filter.measure_type = "continuous"
    pheno_filters.sample_continuous_filter.filter_type = "multi"
    pheno_filters.sample_continuous_filter.role = "prb"

After adding the phenotype filters configuration, restart the web server and
navigate to the Genotype Browser. You should be able to see the Advanced option
under the Family Filters - this is where the phenotype filters can be applied.

Configure Phenotype Columns in Genotype Browser
+++++++++++++++++++++++++++++++++++++++++++++++

Phenotype columns contain values from a phenotype database.
These values are selected from the individual who has the variant displayed in the :ref:`genotype_browser_ui`'s table preview.
They can be added when a phenotype database is attached to a study.

Let's add a phenotype column. To do this, you need to define it in the study's config,
in the genotype browser section:

.. code::

    [genotype_browser]
    (...)

    selected_pheno_column_values = ["pheno"]

    pheno.pheno.name = "Measures"
    pheno.pheno.slots = [
        {role = "prb", source = "i1.age", name = "Age"},
        {role = "prb", source = "i1.iq", name = "Iq"}
    ]

For the phenotype columns to be in the Genotype Browser table preview or download file, 
they have to be present in the ``preview_columns`` or the ``download_columns`` in the Genotype Browser
configuration. Add this in the genotype section:

.. code::

    preview_columns = ["family", "variant", "genotype", "effect", "weights", "mpc_cadd", "freq", "pheno"]


Enabling the Phenotype Tool
+++++++++++++++++++++++++++

To enable the :ref:`phenotype_tool_ui` for a study, you must edit
the study's configuration file and set the appropriate property, as with
the :ref:`phenotype_browser_ui`. Open the configuration file ``comp_all.conf``
and add the following line:

.. code::

    phenotype_tool = true

After editing, it should look like this:

.. code::

    id = "comp_all"
    conf_dir = "."
    has_denovo = true
    phenotype_browser = true
    phenotype_data = "comp_pheno"
    phenotype_tool = true


Restart the GPF web server and select the ``comp_all`` study.
You should see the :ref:`phenotype_tool_ui` tab. Once you have selected it, you
can select a phenotype measure of your choice. To get the tool to acknowledge
the variants in the ``comp_all`` study, select the `All` option of the
`Present in Parent` field. Since the effect types of the variants in the comp
study are only `Missense` and `Synonymous`, you may wish to de-select the
`LGDs` option under the `Effect Types` field. There are is also the option to
normalize the results by one or two measures configured as regressors - age and
non-verbal IQ.

Click on the `Report` button to produce the results.


Dataset Statitistics and de Novo Gene Sets
##########################################

.. _reports_tool:

Generate Variant Reports
++++++++++++++++++++++++

To generate family and de Novo variant reports, you can use
the ``generate_common_report.py`` tool. It supports the option ``--show-studies``
to list all studies and datasets configured in the GPF instance::

    generate_common_report.py --show-studies

To generate the reports for a given configured study, you can use the ``--studies`` option.
For example, to generate the reports for the `comp_all` study, you should use::

    generate_common_report.py --studies comp_all


Generate Denovo Gene Sets
+++++++++++++++++++++++++

To generate de Novo gene sets, you can use the
``generate_denovo_gene_sets.py`` tool. Similar to :ref:`reports_tool` above,
you can use the ``--show-studies`` and ``--studies`` option.

To generate the de Novo gene sets for the `comp_all` study::

    generate_denovo_gene_sets.py --studies comp_all


Getting Started with Annotation Pipeline
########################################

Get Genomic Scores Database
+++++++++++++++++++++++++++

To annotate variants with genomic scores, you will need a genomic scores
database or at least genomic scores you plan to use. You can find some
genomic scores for HG19 `here <https://iossifovlab.com/distribution/public/genomic-scores-hg19/>`_.

Navigate to the genomic-scores-hg19 folder:

.. code::

    cd gpf_test/genomic-scores-hg19


Download and untar the genomic scores you want to use. For example, if you want to use
`gnomAD_exome` and `MPC` frequencies:

.. code:: bash

    wget -c https://iossifovlab.com/distribution/public/genomic-scores-hg19/gnomAD_exome-hg19-latest.tar
    wget -c https://iossifovlab.com/distribution/public/genomic-scores-hg19/MPC-hg19-latest.tar
    tar xvf gnomAD_exome-hg19-latest.tar
    tar xvf MPC-hg19-latest.tar

This will create two subdirectories inside the ``genomic-scores-hg19``
directory, which contain `gnomAD_exome` frequencies and `MPC` genomic scores
prepared to be used by the GPF annotation pipeline and import tools.

Annotation configuration
++++++++++++++++++++++++

If you want to use genomic scores for annotation of the variants
you are importing, you must make appropriate changes in the GPF annotation
pipeline configuration file:

.. code::

    gpf_test/annotation.conf

This configuration pipeline contains some examples on how to configure
annotation with `MPC` and `CADD` genomic scores and
for `gnomAD exome` and `gnomAD genome` frequencies. Uncomment
the appropriate example and adjust it according to your needs.

.. note::
    The genomic scores folders inside the directory generated by
    ``wdae_bootstrap.sh`` - ``genomic-scores-hg19`` and ``genomic-scores-hg38`` are
    the default locations where the annotation pipeline will resolve the
    interpolation strings ``%(scores_hg19_dir)s`` and
    ``%(scores_hg38_dir)s``, respectively. These interpolation strings are used
    when specifying the location of the genomic score source file to use
    (e.g. ``%(scores_hg19_dir)s/CADD/CADD.bedgraph.gz``).

    You can put your genomic scores inside these directories, or you can specify a
    custom ``scores_hg19_dir`` path at the top of the annotation configuration
    file. Note that this will break genomic scores which were configured
    using the old path.

For example if you want to annotate variants with `gnomAD_exome` frequencies and
`MPC` genomic scores the ``annotation.conf`` file should be edited in the following
way:


.. code::

    [vars]
    scores_hg19_dir = "/home/user/gpf_test/genomic-scores-hg19"

    ##############################
    [[sections]]

    annotator = "effect_annotator.VariantEffectAnnotator"

    options.mode = "replace"

    columns.effect_type = "effect_type"

    columns.effect_genes = "effect_genes"
    columns.effect_gene_genes = "effect_gene_genes"
    columns.effect_gene_types = "effect_gene_types"

    columns.effect_details = "effect_details"
    columns.effect_details_transcript_ids = "effect_details_transcript_ids"
    columns.effect_details_details = "effect_details_details"

    ##############################
    [[sections]]

    annotator = "score_annotator.NPScoreAnnotator"

    options.scores_file = "%(scores_hg19_dir)s/MPC/fordist_constraint_official_mpc_values_v2.txt.gz"

    columns.MPC = "mpc"

    ##############################
    [[sections]]

    annotator = "frequency_annotator.FrequencyAnnotator"

    options.scores_file = "%(scores_hg19_dir)s/gnomAD_exome/gnomad.exomes.r2.1.sites.tsv.gz"

    columns.AF = "exome_gnomad_af"
    columns.AF_percent = "exome_gnomad_af_percent"

    columns.AC = "exome_gnomad_ac"
    columns.AN = "exome_gnomad_an"
    columns.controls_AC = "exome_gnomad_controls_ac"
    columns.controls_AN = "exome_gnomad_controls_an"
    columns.controls_AF = "exome_gnomad_controls_af"
    columns.non_neuro_AC = "exome_gnomad_non_neuro_ac"
    columns.non_neuro_AN = "exome_gnomad_non_neuro_an"
    columns.non_neuro_AF = "exome_gnomad_non_neuro_af"
    columns.controls_AF_percent = "exome_gnomad_controls_af_percent"
    columns.non_neuro_AF_percent = "exome_gnomad_non_neuro_af_percent"

After updating the annotation configuration file,
we need to reimport the studies in order for the changes to take effect.
To demonstrate, let's reimport the `iossifov_2014` study. Go to the directory
in which you downloaded it:

.. code::

    cd iossifov_2014/

And run the ``simple_study_import.py`` command: 

.. code::

    simple_study_import.py IossifovWE2014.ped \
        --id iossifov_2014 \
        --denovo-file IossifovWE2014.tsv

After the import is finished, restart the GPF web server:

.. code::

    wdaemanage.py runserver 0.0.0.0:8000


.. _impala_storage:

Using Apache Impala as storage
##############################

Starting Apache Impala
++++++++++++++++++++++

To start a local instance of Apache Impala you will need an installed `Docker <https://www.docker.com/get-started>`_.

.. note::
   If you are using Ubuntu, you can use the following `instructions <https://docs.docker.com/install/linux/docker-ce/ubuntu/>`_
   to install Docker.

We provide a Docker container with Apache Impala. To run it, you can use the script::

    run_gpf_impala.sh

This script pulls out the container's image from
`dockerhub <https://cloud.docker.com/u/seqpipe/repository/docker/seqpipe/seqpipe-docker-impala>`_
and runs it under the name "gpf_impala". When the container is ready,
the script will print the following message::

    ...
    ===============================================
    Local GPF Apache Impala container is READY...
    ===============================================


.. note::
    In case you need to stop this container, you can use the command ``docker stop gpf_impala``.
    For starting the container, use ``run_gpf_impala.sh``.

.. note::
    Here is a list of some useful Docker commands:

        - ``docker ps`` shows all running docker containers

        - ``docker logs -f gpf_impala`` shows the log from the "gpf_impala" container

        - ``docker start gpf_impala`` starts the "gpf_impala" container

        - ``docker stop gpf_impala`` stops the "gpf_impala" container

        - ``docker rm gpf_impala`` removes the "gpf_impala" container (only if stopped)

.. note::
    The following ports are used by the "gpf_impala" container:

        - 8020 - for accessing HDFS
        - 9870 - for Web interface to HDFS Named Node
        - 9864 - for Web interface to HDFS Data Node
        - 21050 - for accessing Impala
        - 25000 - for Web interface to Impala daemon
        - 25010 - for Web interface to Impala state store
        - 25020 - for Web interface to Impala catalog

    Please make sure these ports are not in use on the host where you are going to start the "gpf_impala" container.


Configuring the Apache Impala storage
+++++++++++++++++++++++++++++++++++++

The available storages are configured in ``DAE.conf``.
This is an example section which configures an Apache Impala storage.

.. code:: none

    [storage.test_impala]
    storage_type = "impala"
    impala.host = "localhost"
    impala.port = 21050
    impala.db = "gpf_test_db"
    hdfs.host = "localhost"
    hdfs.port = 8020
    hdfs.base_dir = "/user/test_impala/studies"
    dir = "/tmp/test_impala/studies"

Importing studies into Impala
+++++++++++++++++++++++++++++

The simple study import tool has an optional argument to specify the storage
you wish to use. You can pass the ID of the Apache Impala storage configured
in ``DAE.conf`` earlier.

.. code:: none

  --genotype-storage <genotype storage id>
                        Id of defined in DAE.conf genotype storage [default:
                        genotype_impala]


Example Usage of GPF Python Interface
#####################################

The simplest way to start using GPF's Python API is to import the ``GPFInstance``
class and instantiate it:

.. code-block:: python3

    from dae.gpf_instance.gpf_instance import GPFInstance
    gpf_instance = GPFInstance()

This ``gpf_instance`` object groups together a number of objects, each dedicated
to managing different parts of the underlying data. It can be used to interact
with the system as a whole.

For example, to list all studies configured in the startup GPF instance, use:

.. code-block:: python3

    gpf_instance.get_genotype_data_ids()

This will return a list with the ids of all configured studies:

.. code-block:: python3

    ['comp_vcf',
     'comp_denovo',
     'comp_all',
     'iossifov_2014']

To get a specific study and query it, you can use:

.. code-block:: python3

    st = gpf_instance.get_genotype_data('comp_denovo')
    vs = list(st.query_variants())

.. note::
    The `query_variants` method returns a Python iterator.

To get the basic information about variants found by the ``query_variants`` method,
you can use:

.. code-block:: python3

    for v in vs:
        for aa in v.alt_alleles:
            print(aa)

    1:865664 G->A f1
    1:865691 C->T f3
    1:865664 G->A f3
    1:865691 C->T f2
    1:865691 C->T f1

The ``query_variants`` interface allows you to specify what kind of variants
you are interested in. For example, if you only need "splice-site" variants, you
can use:

.. code-block:: python3

    st = gpf_instance.get_genotype_data('iossifov_2014')
    vs = st.query_variants(effect_types=['splice-site'])
    vs = list(vs)
    print(len(vs))

    >> 87

Or, if you are interested in "splice-site" variants only in people with
"prb" role, you can use:

.. code-block:: python3

    vs = st.query_variants(effect_types=['splice-site'], roles='prb')
    vs = list(vs)
    len(vs)

    >> 62
