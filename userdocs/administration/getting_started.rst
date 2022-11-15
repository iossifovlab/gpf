GPF Getting Started Guide
=========================


Prerequisites
#############

This guide assumes that you are working on a recent Linux box.


Working version of `anaconda` or `miniconda`
++++++++++++++++++++++++++++++++++++++++++++

The GPF system is distributed as an Anaconda package using the `conda`
package manager.

If you do not have a working version of Anaconda or Miniconda, you must
install one. We recommended using a Miniconda version.

Go to the Miniconda 
`distribution page <https://docs.conda.io/en/latest/miniconda.html>`_,
download the Linux installer

.. code-block:: bash

    wget -c https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

and install it in your local environment:

.. code-block:: bash

    sh Miniconda3-latest-Linux-x86_64.sh

.. note::

    At the end of the installation process, you will be asked if you wish
    to allow the installer to initialize Anaconda3 by running `conda` init.
    If you choose to, every terminal you open after that will have the ``base``
    Anaconda environment activated, and you'll have access to the ``conda``
    commands used below.

Once Anaconda/Miniconda is installed, we would recommend installing ``mamba`` 
instead of ``conda``. Mamba will speed up the installation of packages:

.. code-block::

    conda install -c conda-forge mamba


GPF Installation
################

The GPF system is developed in Python and supports Python 3.9 and up.
The recommended way to set up the GPF development environment is to use Anaconda.

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

    mamba install \
        -c defaults \
        -c conda-forge \
        -c bioconda \
        -c iossifovlab \
        gpf_wdae

This command is going to install GPF and all of its dependencies.

.. note:: 

    If you want to install a development version of GPF, you can use
    the following command:

    .. code-block:: bash

        mamba install \
            -c defaults \
            -c conda-forge \
            -c bioconda \
            -c iossifovlab/label/dev \
            -c iossifovlab gpf_wdae


Create an empty GPF instance
++++++++++++++++++++++++++++

Create an empty directory named ``data-hg38-empty``:

.. code-block:: bash

    mkdir data-hg38-empty

and inside it, create a file named ``gpf_instance.yaml`` with the following
content:

.. code-block:: yaml

    reference_genome:
        resource_id: "hg38/genomes/GRCh38-hg38"

    gene_models:
        resource_id: "hg38/gene_models/refSeq_v20200330"

This will create a GPF instance that:

* The reference genome used by this GPF instance is ``hg38/genomes/GRCh38-hg38``
  from default GRR;

* The gene models used by this GPF instance are 
  ``hg38/gene_models/refSeq_v20200330`` from default GRR;

* If not specified otherwise, the GPF uses the default genomic resources
  repository located at 
  `https://www.iossifovlab.com/distribution/public/genomic-resources-repository/ 
  <https://www.iossifovlab.com/distribution/public/genomic-resources-repository/>`_.
  Resources are used without caching.



Prepare the GPF web server
##########################

By default, the GPF system looks for a file ``gpf_instance.yaml`` in the
current directory (and its parent directories). If GPF finds such a file, it
uses it as a configuration for the GPF instance. Otherwise, it throws an
exception.

Now we can run the GPF development web server and browse our empty GPF instance:

.. code-block:: bash

    wgpf run

and browse the GPF development server at ``http://localhost:8000``.


To stop the development GPF web server, you should press ``Ctrl-C`` - the usual
keybinding for stopping long-running Linux commands in a terminal.


.. warning:: 

    The development web server run by ``wgpf run`` used in this guide
    is meant for development purposes only
    and is not suitable for serving the GPF system in production.


Import genotype variants
########################


Data Storage
++++++++++++


The GPF system uses genotype storage for storing genomic variants.

We are going to use in-memory genotype storage for this guide. It is easiest
to set up and use, but it is unsuitable for large studies.

By default, each GPF instance has internal in-memory genotype storage.

Import Tools and Import Project
+++++++++++++++++++++++++++++++

Importing genotype data into a GPF instance involves multiple steps. 
The tool used to import genotype data is named `import_tool`. This tool
expects an import project file that describes the import.

This tool supports importing variants from three formats:

* List of de Novo variants

* Variant Call Format (VCF)

* CSHL transmitted variants format

* CNV variants


Example import of de Novo variants: ``helloworld``
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. note:: 

    Input files for this example can be downloaded from 
    `denovo-helloworld.tar.gz <https://iossifovlab.com/distribution/public/denovo-helloworld.tar.gz>`_.
    
Let us import a small list of de Novo variants. We will need the list of
de Novo variants ``helloworld.tsv``:

.. code-block::

    CHROM   POS	      REF    ALT  person_ids
    chr14   21403214  T      C    p1
    chr14   21431459  G      C    p1
    chr14   21391016  A      AT   p2
    chr14   21403019  G      A    p2
    chr14   21402010  G      A    p1
    chr14   21393484  TCTTC  T    p2

and a pedigree file that describes the families ``helloworld.ped``:

.. code-block::

    familyId  personId  dadId   momId   sex   status  role  phenotype
    f1        m1        0       0       2     1       mom   unaffected
    f1        d1        0       0       1     1       dad   unaffected
    f1        p1        d1      m1      1     2       prb   autism
    f1        s1        d1      m1      2     2       sib   unaffected
    f2        m2        0       0       2     1       mom   unaffected
    f2        d2        0       0       1     1       dad   unaffected
    f2        p2        d2      m2      1     2       prb   autism


The project configuration file for importing this study
``denovo_helloworld.yaml`` should look like:

.. code-block:: yaml

    id: denovo_helloworld

    input:
      pedigree:
        file: helloworld.ped

      denovo:
        files:
        - helloworld.tsv
        person_id: person_ids
        chrom: CHROM
        pos: POS
        ref: REF
        alt: ALT    


To import this project run the following command:

.. code-block:: bash

    import_tool -f denovo_helloworld.yaml


When the import finishes you can run the GPF development server using:

.. code-block:: bash

    wpgf run

and browse the content of the GPF development server at `http://localhost:8000`


Example import of VCF variants: ``vcf_helloworld``
++++++++++++++++++++++++++++++++++++++++++++++++++


.. note:: 

    Input files for this example can be downloaded from 
    `vcf-helloworld.tar.gz <https://iossifovlab.com/distribution/public/vcf-helloworld.tar.gz>`_.


Let us have a small VCF file ``hellowrold.vcf``:

.. code-block::

  ##fileformat=VCFv4.2
  ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
  ##contig=<ID=chr14>
  #CHROM POS      ID REF  ALT QUAL FILTER INFO FORMAT m1  d1  p1  s1  m2  d2  p2
  chr14  21385738 .  C    T   .    .      .    GT     0/0 0/1 0/1 0/0 0/0 0/1 0/0   
  chr14  21385954 .  A    C   .    .      .    GT     0/0 0/0 0/0 0/0 0/1 0/0 0/1   
  chr14  21393173 .  T    C   .    .      .    GT     0/1 0/0 0/0 0/1 0/0 0/0 0/0   
  chr14  21393702 .  C    T   .    .      .    GT     0/0 0/0 0/0 0/0 0/0 0/1 0/1   
  chr14  21393860 .  G    A   .    .      .    GT     0/0 0/1 0/1 0/1 0/0 0/0 0/0   
  chr14  21403023 .  G    A   .    .      .    GT     0/0 0/1 0/0 0/1 0/1 0/0 0/0   
  chr14  21405222 .  T    C   .    .      .    GT     0/0 0/0 0/0 0/0 0/0 0/1 0/0   
  chr14  21409888 .  T    C   .    .      .    GT     0/1 0/0 0/1 0/0 0/1 0/0 1/0   
  chr14  21429019 .  C    T   .    .      .    GT     0/0 0/1 0/1 0/0 0/0 0/1 0/1   
  chr14  21431306 .  G    A   .    .      .    GT     0/0 0/1 0/1 0/1 0/0 0/0 0/0   
  chr14  21431623 .  A    C   .    .      .    GT     0/0 0/0 0/0 0/0 0/1 1/1 1/1   
  chr14  21393540 .  GGAA G   .    .      .    GT     0/1 0/1 1/1 0/0 0/0 0/0 0/0   

and a pedigree file ``helloworld.ped`` (the same pedigree file used in 
`Example import of de Novo variants: ``helloworld```_):

.. code-block::

    familyId  personId  dadId   momId   sex   status  role  phenotype
    f1        m1        0       0       2     1       mom   unaffected
    f1        d1        0       0       1     1       dad   unaffected
    f1        p1        d1      m1      1     2       prb   autism
    f1        s1        d1      m1      2     2       sib   unaffected
    f2        m2        0       0       2     1       mom   unaffected
    f2        d2        0       0       1     1       dad   unaffected
    f2        p2        d2      m2      1     2       prb   autism


The project configuration file for importing this VCF study
``vcf_helloworld.yaml`` should look like:

.. code-block:: yaml

    id: vcf_helloworld

    input:
      pedigree:
        file: helloworld.ped

      vcf:
        files:
        - helloworld.vcf

To import this project run the following command:

.. code-block:: bash

    import_tool -f vcf_helloworld.yaml


When the import finishes you can run the GPF development server using:

.. code-block:: bash

    wpgf run

and browse the content of the GPF development server at `http://localhost:8000`


Example of a dataset (group of genotype studies)
++++++++++++++++++++++++++++++++++++++++++++++++

The already imported studies ``denovo_helloworld`` and ``vcf_helloworld``
have genomic variants for the same group of individuals ``helloworld.ped``.
We can create a dataset (group of genotype studies) that include both studies.

To this end create a directory ``datasets/helloworld`` inside the GPF instance
directory ``data-hg38-empty``:

.. code-block:: bash

    cd data-hg38-empty
    mkdir -p datasets/helloworld

and place the following configuration file ``hellowrold.yaml`` inside that
directory:

.. code-block:: yaml

    id: helloworld
    name: Hello World Dataset
    
    studies:
      - denovo_helloworld
      - vcf_helloworld    



Example import of de Novo variants from `Rates of contributory de novo mutation in high and low-risk autism families`
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Let us import de Novo variants from the 
`Yoon, S., Munoz, A., Yamrom, B. et al. Rates of contributory de novo mutation
in high and low-risk autism families. Commun Biol 4, 1026 (2021). 
<https://doi.org/10.1038/s42003-021-02533-z>`_.

We will focus on de Novo variants from the SSC collection published in the 
aforementioned paper.
To import these variants into the GPF system we need a list of de Novo variants
and a pedigree file describing the families.
The list of de Novo variants is available from 
`Supplementary Data 2 <https://static-content.springer.com/esm/art%3A10.1038%2Fs42003-021-02533-z/MediaObjects/42003_2021_2533_MOESM4_ESM.xlsx>`_.
The pedigree file for this study is not available. Instead, we have a list of
children available from `Supplementary Data 1 <https://static-content.springer.com/esm/art%3A10.1038%2Fs42003-021-02533-z/MediaObjects/42003_2021_2533_MOESM3_ESM.xlsx>`_.

Let us first export these Excel spreadsheets into CSV files. Let us say that the
list of de Novo variants from the SSC collection is saved into a file named
``SupplementaryData2_SSC.tsv`` and the list of children is saved into a TSV file
named ``SupplementaryData1_Children.tsv``.

.. note:: 

    Input files for this example can be downloaded from 
    `denovo-in-high-and-low-risk-papter.tar.gz <https://iossifovlab.com/distribution/public/denovo-in-high-and-low-risk-papter.tar.gz>`_.





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

After this, the beginning of the configuration file should look like this:

.. code::

    id = "comp_all"
    conf_dir = "."
    has_denovo = true
    phenotype_browser = true
    phenotype_data = "comp_pheno"

When you restart the server, you should be
able to see the 'Phenotype Browser' tab in the `comp_all` study.

Configure Family Filters in Genotype Browser
+++++++++++++++++++++++++++++++++++++++++++++++

A study or a dataset can have phenotype filters configured for its :ref:`genotype_browser_ui`
when it has a phenotype database attached to it. The configuration looks like this:

.. code::

    [genotype_browser]
    enabled = true
    
    family_filters.sample_continuous_filter.name = "Sample Filter Name"
    family_filters.sample_continuous_filter.from = "phenodb"
    family_filters.sample_continuous_filter.source_type = "continuous"
    family_filters.sample_continuous_filter.filter_type = "multi"
    family_filters.sample_continuous_filter.role = "prb"

After adding the family filters configuration, restart the web server and
navigate to the Genotype Browser. You should be able to see the Advanced option
under the Family Filters - this is where the family filters can be applied.

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
configuration. Add this in the genotype_browser section:

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

Below is a sample config for annotating with MPC, gnomAD exome and gnomAD genome
scores. Overwrite the current config with the snippet below.

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
    dir = "/tmp/test_impala/studies"
    
    impala.hosts = ["localhost"]
    impala.port = 21050
    impala.db = "gpf_test_db"
    
    hdfs.host = "localhost"
    hdfs.port = 8020
    hdfs.base_dir = "/user/test_impala/studies"

Importing studies into Impala
+++++++++++++++++++++++++++++

The simple study import tool has an optional argument to specify the storage
you wish to use. You can pass the ID of the Apache Impala storage configured
in ``DAE.conf`` earlier.

.. code:: none

  --genotype-storage <genotype storage id>
                        Id of defined in DAE.conf genotype storage [default:
                        genotype_impala]

For example, to import the IossifovWE2014 study into the "test_impala" storage,
the following command is used:

.. code:: none

    simple_study_import.py IossifovWE2014.ped \
        --id iossifov_2014 \
        --denovo-file IossifovWE2014.tsv \
        --genotype-storage test_impala


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
