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

Download Anaconda from the Anaconda's `distribution page <https://www.anaconda.com/distribution>`_.

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
    └── wdae


Run GPF web server
##################

Enter into ``gpf_test/`` and source ``setenv.sh`` file:

.. code-block:: bash

    cd gpf_test/
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
the GPF instance, we will reproduce the necessary steps for importing
the `comp` study data.

Data Storage
++++++++++++

By default, GPF uses the filesystem for storing imported genotype data.
This is fine for smaller sized studies - however, there is an option to use
Apache Impala as storage. This can be especially useful for larger studies.
If you wish to use Apache Impala as storage, refer to :ref:`impala-storage`.

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


Example import of variants
**************************

Let's say you have a pedigree file ``comp.ped`` describing family information,
a VCF file ``comp.vcf`` with transmitted variants and a list of de Novo
variants ``comp.tsv``. The example data can be downloaded from `here <https://iossifovlab.com/distribution/public/studies/>`_.

.. note::
    Make sure not to download in the gpf_test/studies folder, as this is where
    the system imports and reads its data to/from.

To import this data as a study into the GPF instance:

* Download the ``comp`` demo study and extract the download archive::

    wget -c https://iossifovlab.com/distribution/public/studies/genotype-comp-latest.tar.gz
    tar zxvf genotype-comp-latest.tar.gz

* Enter into the created directory ``comp``::

    cd comp

* Run ``simple_study_import.py`` to import the VCF variants; this command uses
  three arguments - study ID to use, pedigree file name and VCF file name::

        simple_study_import.py comp.ped \
            --id comp_vcf \
            --vcf-files comp.vcf

  | This command creates a study with ID `comp_vcf` that contains all VCF variants.

* Run ``simple_study_import.py`` to import the de Novo variants; this command
  uses three arguments - study ID to use, pedigree file name and de Novo variants file name::

        simple_study_import.py comp.ped \
            --id comp_denovo \
            --denovo-file comp.tsv

  | This command creates a study with ID `comp_denovo` that contains all de Novo variants.

* Run ``simple_study_import.py`` to import all VCF and de Novo variants;
  this command uses four arguments - study ID to use, pedigree file name,
  VCF file name and de Novo variants file name::

        simple_study_import.py comp.ped \
            --id comp_all \
            --denovo-file comp.tsv \
            --vcf-files comp.vcf

  This command creates a study with ID `comp_all` that contains all
  VCF and de Novo variants.


.. note::
    The expected format for the de Novo variants file is a tab separated
    file that contains following columns:

    - familyId - family Id matching a family from the pedigree file
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

As an example of importing study with de Novo variants, you can use the `iossifov_2014` study.
Download and extract the study::

    wget -c https://iossifovlab.com/distribution/public/studies/genotype-iossifov_2014-latest.tar.gz
    tar zxf genotype-iossifov_2014-latest.tar.gz

Enter into the created directory ``iossifov_2014``::

    cd iossifov_2014

and run ``simple_study_import.py`` tool::

    simple_study_import.py IossifovWE2014.ped \
        --id iossifov_2014 \
        --denovo-file IossifovWE2014.tsv

To see the imported variants, restart the GPF development web server and find the
`iossifov_2014` study.


Getting Started with Enrichment Tool
####################################

For studies, that include de Novo variants you can enable the :ref:`enrichment_tool_ui`.
As an example, let us enable it for the already imported
`iossifov_2014` study.

Go to the directory where the configuration file of the `iossifov_2014`
study is located::

    cd gpf_test/studies/iossifov_2014

Edit the study configuration file ``iossifov_2014.conf`` and add this new section in the end of the file::

    [enrichment]
    enabled = true

Restart the `wdaemanage.py`::

    wdaemanage.py runserver 0.0.0.0:8000

Now when you navigate to the iossifov_2014 study in the browser, you should be able to
use the `Enrichment Tool` under the 'Enrichment Tool' tab.


Getting Started with Preview Columns
####################################

For each study we can specify the columns that are shown in the preview of
variants and in the downloaded variants.

As an example we are going to redefine `Frequency` column in `comp_vcf`
study imported in previous example.

.. code::

    cd gpf_test/studies/comp_vcf


Edit the configuration file ``comp_vcf.conf`` and add the following lines:

.. code::

    [genotype_browser]
    genotype.freq.name = "Frequency"
    genotype.freq.slots = 
        [{source = "exome_gnomad_af_percent", name = "exome gnomad", format = "E %%.3f"},
        {source = "genome_gnomad_af_percent", name = "genome gnomad", format = "G %%.3f"},
        {source = " af_allele_freq", name = "study freq", format = "S %%.3f"}]

This overwrites the definition of existing preview column `Frequency` to
include not only the gnomAD frequencies, but also to include allele frequency.


Getting Started with Phenotype Data
###################################

Simple Pheno Import Tool
++++++++++++++++++++++++

The GPF simple pheno import tool prepares phenotype data to be used by the GPF
system.

As and example we are going to show how to import simulated demo phenotype 
data into our demo GPF instance. We are going to use simulated
phenotype data available `here <https://iossifovlab.com/distribution/public/pheno/phenotype-comp-data-latest.tar.gz>`_.

Download the archive and extract it outside of GPF instance data directory:

.. code::

    wget -c https://iossifovlab.com/distribution/public/pheno/phenotype-comp-data-latest.tar.gz
    tar zxvf phenotype-comp-data-latest.tar.gz

Enter into the created directory ``comp-data``::

    cd comp-data

Files that are available in that directory are:

* | ``comp_pheno.ped`` - the pedigree file for all families included into the
   database;

* ``instruments`` - directory, containing all instruments;

* ``instruments/i1.csv`` - all measurements for instrument ``i1``.

* ``comp_pheno_data_dictionary.tsv`` - descriptions for all measurements

* ``comp_pheno_regressions.conf`` - regression configuration file

The easiest way to import this phenotype database into the GPF instance is to
use the `simple_pheno_import.py` tool. It combines converting phenotype
instruments and measures into a GPF phenotype database and generates data and
figures needed for the :ref:`phenotype_browser_ui`. It will import the phenotype database
directly to the DAE data directory specified in your environment.

.. code::

    simple_pheno_import.py -p comp_pheno.ped \
        -i instruments/ -d comp_pheno_data_dictionary.tsv -o comp_pheno \
        --regression comp_pheno_regressions.conf

Options used in this command are as follows:

* ``-p`` option allows to specify the pedigree file;

* | ``-d`` option specifies the name of the data dictionary file for the
   phenotype database

* | ``-i`` option allows to specify the directory where instruments
   are located;

* | ``-o`` options specifies the name of the output phenotype database that
   will be used in the Phenotype Browser;

* | ``--regression`` option specifies a path to a pheno regression config which
   describes a list of measures to make regressions against

You can use ``-h`` option to see all options supported by the
``simple_pheno_import.py`` tool.

Configure Phenotype Database
++++++++++++++++++++++++++++

Phenotype databases have a short configuration file (whose filenames
usually end with the extension ``.conf``) which points
the system to their files, as well as specifying some
other properties. When importing a phenotype database through the
`simple_pheno_import.py` tool, a configuration file is automatically
generated. You may inspect the ``gpf_test/pheno/comp_pheno`` directory
to see the configuration file generated from the import tool:

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
be working with the manually imported ``comp_all`` study.

The phenotype databases could be attached to one or more studies and datasets.
If you want to attach ``comp_pheno`` phenotype
database to ``comp_all`` study, you need to specify it in the study's
configuration file ``comp_all.conf``, which can be found at gpf_test/studies/comp_all.
Edit the file to add this line at the bottom of it. Make sure the line is separated and
that it isn't part of any section. 

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

    [genotype_storage]
    id = "genotype_filesystem"

    [genotype_storage.files]
    pedigree.path = "".../gpf_test/studies/comp_all/data/comp.ped"
    pedigree.params = {}

    [[genotype_storage.files.variants]]
    path = "".../gpf_test/studies/comp_all/data/comp.tsv"
    format = "denovo"
    params = {}

    [[genotype_storage.files.variants]]
    path = "".../gpf_test/studies/comp_all/data/comp.vcf"
    format = "vcf"
    params = {}

    [genotype_browser]
    enabled = true

    phenotype_browser = true
    phenotype_data = "comp_pheno"

.. note::
    Your paths will be different than the ones shown in the configuration above.

When you restart the server, you should be
able to see the 'Phenotype Browser' tab in the `comp_all` study.

Configure Phenotype Filters in Genotype Browser
+++++++++++++++++++++++++++++++++++++++++++++++

A study or a dataset can have Phenotype Filters configured for its :ref:`genotype_browser_ui`
when it has a phenotype database attached to it. The configuration looks like this:

.. code::

    [genotypeBrowser]

    selectedPhenoFiltersValues = sampleContinuousFilter

    phenoFilters.sampleContinuousFilter.name = sampleFilterName
    phenoFilters.sampleContinuousFilter.measureType = continuous
    phenoFilters.sampleContinuousFilter.filter = multi:prb

``selectedPhenoFiltersValues`` is a comma separated list of ids of the defined
Phenotype Filters. Each phenotype filter is expected to have a
``phenoFilters.<pheno_filter_id>`` configuration.

The required configuration options for each pheno filter are:

* | ``phenoFilters.<pheno_filter_id>.name`` - name to use when showing the
   pheno filter in the Genotype Browser table preview.

* | ``phenoFilters.<pheno_filter_id>.measureType`` - the measure type of the
   pheno filter. One of ``continuous``, ``categorical``, ``ordinal`` or
   ``raw``.

* ``phenoFilters.<pheno_filter_id>.filter`` - the definition of the filter.

The definition of a pheno filter has the format
``<filter_type>:<role>(:<measure_id>)``. Each of these

* | ``filter_type`` - either ``single`` or ``multiple``. A single filter is
   used to filter on only one specified measure (specified by
   ``<measure_id>``). A ``multiple`` pheno filter allows the user to choose
   which measure to use for filtering. The available measures depend on the
   ``phenoFilters.<pheno_filter_id>.type`` field.

* | ``role`` - which persons' phenotype data to use for this filter. Ex.
   ``prb`` uses the probands' values for filtering. When the role matches more
   than one person the first is chosen.

* | ``measure_id`` - id of the measure to be used for a ``single`` filter. Not
   used when a ``multiple`` filter is being defined.

After adding the configuration for Phenotype Filters and reloading the Genotype
Browser the Advanced option of the Family Filters should be present.

Configure Phenotype Columns in Genotype Browser
+++++++++++++++++++++++++++++++++++++++++++++++

Phenotype Columns are values from the Phenotype Database for each variant
displayed in :ref:`genotype_browser_ui` table preview. They can be added when a phenotype database
is attached to a study or a dataset.

To add a Phenotype Column you need to define it in the study or dataset config:

.. code::

    [genotypeBrowser]

    selectedPhenoColumnValues = pheno

    pheno.pheno.name = Measures
    pheno.pheno.slots = prb:i1.age:Age,
        prb:i1.iq:Iq

The ``selectedPhenoColumnValues`` property is a comma separated list of ids for
each Pheno Column to display. Each Pheno Column has to have a
``pheno.<measure_id>`` configuration with the following properties:

* | ``pheno.<measure_id>.name`` - the display name of the pheno column group
   used in the Genotype Browser table preview.

* | ``pheno.<measure_id>.slots`` - comma separated definitions for all pheno
   columns.

The Phenotype Column definition has the following structure:
``<role>:<measure_id>:<name>``, where:

* | ``<role>`` - role of the person whose pheno values will be displayed. If
   the role matches two or more people all of their values will be shown,
   separated with a comma.

* ``<measure_id>`` - id of the measure whose values will be displayed.

* ``<name>`` - the name of the sub-column to be displayed.

For the Phenotype Columns to be in the Genotype Browser table preview or download file, 
they have to be present in the ``previewColumns`` or the ``downloadColumns`` in the Genotype Browser
configuration.

.. code::

    previewColumns = family,variant,genotype,effect,weights,mpc_cadd,freq,pheno


In the above ``comp_all`` configuration, the last column ``pheno`` is a
Phenotype Column.

Enabling the Phenotype Tool
+++++++++++++++++++++++++++

To enable the :ref:`phenotype_tool_ui` for a study, you must edit
its configuration file and set the appropriate property, as with
the Phenotype browser. Open the configuration file ``comp_all.conf``
and add the following line, separated from other sections:

.. code::

   phenotype_tool = true


Restart the GPF development web server and select the `comp_all` study.
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
genomic scores for HG19 `here <https://iossifovlab.com/distribution/public/genomic-scores-hg19/>`_.

Navigate into the genomic-scores-hg19 folder:

.. code::

    cd gpf_test/genomic-scores-hg19


Download and untar the genomic scores you want to use. For example, if you want to use
`gnomAD_exome` and `gnomAD_genome` frequencies:

.. code:: bash

    wget -c https://iossifovlab.com/distribution/public/genomic-scores-hg19/gnomAD_exome-hg19-latest.tar
    wget -c https://iossifovlab.com/distribution/public/genomic-scores-hg19/MPC-hg19-latest.tar
    tar xvf gnomAD_exome-hg19-latest.tar
    tar xvf MPC-hg19-latest.tar

This will create two subdirectories inside the ``genomic-scores-hg19``
directory, that contain `gnomAD_exome` frequencies and `MPC` genomic scores
prepared to be used by GPF annotation pipeline and GPF import tools.

Annotation configuration
++++++++++++++++++++++++

If you want to use some genomic scores for annotation of the variants
you are importing, you must make appropriate changes in GPF annotation
pipeline configuration file:

.. code::

    gpf_test/annotation.conf

This configuration pipeline contains some examples on how to configure
annotation with `MPC` and `CADD` genomic scores and
for `gnomAD exome` and `gnomAD genome` frequencies. Comment out
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
    file. Beware that this will likely break genomic scores which were specified
    using the old path.

For example if you want to annotate variants with `gnomAD_exome` frequencies and
`MPC` genomic scores the ``annotation.conf`` file should be edited in the following
way:

.. code::
    
    [DEFAULT]

    ################################
    [VariantEffectAnnotation]

    annotator=effect_annotator.VariantEffectAnnotator

    columns.effect_type=effect_type

    columns.effect_genes=effect_genes
    columns.effect_gene_genes=effect_gene_genes
    columns.effect_gene_types=effect_gene_types

    columns.effect_details=effect_details
    columns.effect_details_transcript_ids=effect_details_transcript_ids
    columns.effect_details_details=effect_details_details

    ##############################
    [MPC Genomic Score]
    
    annotator=score_annotator.NPScoreAnnotator
    
    options.scores_file=%(scores_hg19_dir)s/MPC/fordist_constraint_official_mpc_values_v2.txt.gz
    
    columns.MPC=mpc

    ######################################
    [gnomAD Exome Frequencies]

    annotator=frequency_annotator.FrequencyAnnotator

    options.scores_file=%(scores_hg19_dir)s/gnomAD_exome/gnomad.exomes.r2.1.sites.tsv.gz

    columns.AF=exome_gnomad_af
    columns.AF_percent=exome_gnomad_af_percent

    columns.AC=exome_gnomad_ac
    columns.AN=exome_gnomad_an
    columns.controls_AC=exome_gnomad_controls_ac
    columns.controls_AN=exome_gnomad_controls_an
    columns.controls_AF=exome_gnomad_controls_af
    columns.non_neuro_AC=exome_gnomad_non_neuro_ac
    columns.non_neuro_AN=exome_gnomad_non_neuro_an
    columns.non_neuro_AF=exome_gnomad_non_neuro_af
    columns.controls_AF_percent=exome_gnomad_controls_af_percent
    columns.non_neuro_AF_percent=exome_gnomad_non_neuro_af_percent

The ``VariantEffectAnnotation`` section defines how the variant effect 
annotation and should not be changed. Next section ``MPC Genomic Score``
defines annotation with MPC genomic score. The last section 
``gnomAD Exome Frequencies`` specifies which of the gnomAD exome frequencies
are used in the annotation.

After updating the annotation configuration file,
we need to reimport the studies in order for the changes to take effect.
To demonstrate, let's reimport the `iossifov_2014` study. Go to the iossifov_2014 directory:

.. code::

    cd iossifov_2014/

And run the ``simple_study_import.py`` command: 

.. code::

    simple_study_import.py IossifovWE2014.ped \
        --id iossifov_2014 \
        --denovo-file IossifovWE2014.tsv

After the import is finished, restart the GPF development server:

.. code::

    wdaemanage.py runserver 0.0.0.0:8000


Using Apache Impala as storage
##############################

Starting Apache Impala
++++++++++++++++++++++

To start a local instance of Apache Impala you will need an `installed Docker <https://www.docker.com/get-started>`_.

.. note::
   If you are using Ubuntu, you can use the following `instructions <https://docs.docker.com/install/linux/docker-ce/ubuntu/>`_
   to install Docker.

To make using GPF
easier, we provide a Docker container with Apache Impala. To run it, you
can use the script::

    run_gpf_impala.sh

This script pulls out Apache Impala image from
`dockerhub <https://cloud.docker.com/u/seqpipe/repository/docker/seqpipe/seqpipe-docker-impala>`_,
creates and starts Docker container named `gpf_impala`
containing all the components needed for running Apache Impala. When the
Apache Impala container is ready for use the script will print a message::

    ...
    ===============================================
    Local GPF Apache Impala container is READY...
    ===============================================


.. note::
    In case you need to stop this container you can
    use Docker commands `docker stop gpf_impala`. For starting the `gpf_impala`
    container use `run_gpf_impala.sh`.

.. note::
    Here is a list of some useful Docker commands:

        - `docker ps` shows all running docker containers;

        - `docker logs -f gpf_impala` shows log from `gpf_impala` container;

        - `docker stop gpf_impala` stops the running `gpf_impala` container;

        - `docker start gpf_impala` starts existing stopped `gpf_impala`
          container;

        - `docker rm gpf_impala` removes existing and stopped `gpf_impala`
          container.

.. note::
    Following ports are used by `gpf_impala` container:

        - 8020 - port for accessing HDFS
        - 9870 - port for Web interface to HDFS Named Node
        - 9864 - port for Web interface to HDFS Data Node
        - 21050 - port for accessing Impala
        - 25000 - port for Web interface to Impala daemon
        - 25010 - port for Web interface to Impala state store
        - 25020 - port for Web interface to Impala catalog

    Please make sure that this ports are not in use on the host where you are
    starting `gpf_impala` container.


Configuring the Apache Impala storage
+++++++++++++++++++++++++++++++++++++

The available storages are configured within ``DAE.conf``.
This is an example section which configures an Apache Impala storage.

.. code:: none

    [storage.test_impala]
    type = impala
    impala.host = localhost
    impala.port = 21050
    impala.db = gpf_test_db
    hdfs.host = localhost
    hdfs.port = 8020
    hdfs.base_dir = /user/test_impala/studies
    dir = /tmp/test_impala/studies

Import the study into Impala
++++++++++++++++++++++++++++

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

This should return a list of all studies' IDs:

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
you are interested in. For example, if you only need 'splice-site' variants, you
can use:

.. code-block:: python3

    st = gpf_instance.get_genotype_data('iossifov_2014')
    vs = st.query_variants(effect_types=['splice-site'])
    vs = list(vs)
    print(len(vs))

    >> 85

Or, if you are interested in 'splice-site' variants only in people with role
'prb' you can use:

.. code-block:: python3

    vs = st.query_variants(effect_types=['splice-site'], roles='prb')
    vs = list(vs)
    len(vs)

    >> 60
