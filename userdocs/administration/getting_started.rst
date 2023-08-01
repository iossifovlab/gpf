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
    to allow the installer to initialize Miniconda3 by running `conda` init.
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



Run the GPF development web server
##################################

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


The GPF system uses genotype storages for storing genomic variants.

We are going to use in-memory genotype storage for this guide. It is easiest
to set up and use, but it is unsuitable for large studies.

By default, each GPF instance has internal in-memory genotype storage.

Import Tools and Import Project
+++++++++++++++++++++++++++++++

Importing genotype data into a GPF instance involves multiple steps. 
The tool used to import genotype data is named `import_tools`. This tool
expects an import project file that describes the import.

This tool supports importing variants from three formats:

* List of de novo variants
* List of de novo CNV variants
* Variant Call Format (VCF)



Example import of de novo variants: ``helloworld``
++++++++++++++++++++++++++++++++++++++++++++++++++

.. note:: 

    Input files for this example can be downloaded from 
    :download:`denovo-helloworld.tar.gz <getting_started_files/denovo-helloworld.tar.gz>`.
    
Let us import a small list of de novo variants. We will need the list of
de novo variants ``helloworld.tsv``:

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


.. warning::

    Please note that the default separator for the list of de novo and pedigree
    files is ``TAB``. If you copy these snippets and paste them into
    corresponding files the separators between values most probably will
    become spaces. 
    
    You need to ensure that separators between column values 
    are ``TAB`` symbols.

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

    import_tools denovo_helloworld.yaml


When the import finishes you can run the GPF development server using:

.. code-block:: bash

    wgpf run

and browse the content of the GPF development server at `http://localhost:8000`


Example import of VCF variants: ``vcf_helloworld``
++++++++++++++++++++++++++++++++++++++++++++++++++


.. note:: 

    Input files for this example can be downloaded from 
    :download:`vcf-helloworld.tar.gz <getting_started_files/vcf-helloworld.tar.gz>`.


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
`Example import of de novo variants: ``helloworld```_):

.. code-block::

    familyId  personId  dadId   momId   sex   status  role  phenotype
    f1        m1        0       0       2     1       mom   unaffected
    f1        d1        0       0       1     1       dad   unaffected
    f1        p1        d1      m1      1     2       prb   autism
    f1        s1        d1      m1      2     2       sib   unaffected
    f2        m2        0       0       2     1       mom   unaffected
    f2        d2        0       0       1     1       dad   unaffected
    f2        p2        d2      m2      1     2       prb   autism


.. warning::

    Please note that the default separator for the VCF and pedigree
    files is ``TAB``. If you copy these snippets and paste them into
    corresponding files the separators between values most probably will
    become spaces. 
    
    You need to ensure that separators between column values 
    are ``TAB`` symbols for import to work.

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

    import_tools vcf_helloworld.yaml


When the import finishes you can run the GPF development server using:

.. code-block:: bash

    wgpf run

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



Example import of de novo variants from `Rates of contributory de novo mutation in high and low-risk autism families`
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Let us import de novo variants from the 
`Yoon, S., Munoz, A., Yamrom, B. et al. Rates of contributory de novo mutation
in high and low-risk autism families. Commun Biol 4, 1026 (2021). 
<https://doi.org/10.1038/s42003-021-02533-z>`_.

We will focus on de novo variants from the SSC collection published in the 
aforementioned paper.
To import these variants into the GPF system we need a list of de novo variants
and a pedigree file describing the families.
The list of de novo variants is available from 
`Supplementary Data 2 <https://static-content.springer.com/esm/art%3A10.1038%2Fs42003-021-02533-z/MediaObjects/42003_2021_2533_MOESM4_ESM.xlsx>`_.
The pedigree file for this study is not available. Instead, we have a list of
children available from `Supplementary Data 1 <https://static-content.springer.com/esm/art%3A10.1038%2Fs42003-021-02533-z/MediaObjects/42003_2021_2533_MOESM3_ESM.xlsx>`_.

Let us first export these Excel spreadsheets into CSV files. Let us say that the
list of de novo variants from the SSC collection is saved into a file named
``SupplementaryData2_SSC.tsv`` and the list of children is saved into a TSV file
named ``SupplementaryData1_Children.tsv``.

.. note:: 

    Input files for this example can be downloaded from 
    :download:`denovo-in-high-and-low-risk-papter.tar.gz <getting_started_files/denovo-in-high-and-low-risk-papter.tar.gz>`.

Preprocess the families data
____________________________


To import the data into GPF we need a pedigree file describing the structure
of the families. The ``SupplementaryData1_Children.tsv`` contains only the list
of children. There is no information about their parents. Fortunately for the
SSC collection it is not difficult to build the full families' structures from
the information we have. For the SSC collection if you have a family with ID
``<fam_id>``, then the identifiers of the individuals in the family are going to
be formed as follows:

* mother - ``<fam_id>.mo``;
* father - ``<fam_id>.fa``;
* proband - ``<fam_id>.p1``;
* first sibling - ``<fam_id>.s1``;
* second sibling - ``<fam_id>.s2``.

Another important restriction for SSC is that the only affected person in the 
family is the proband. The affected status of the mother, father and 
siblings are ``unaffected``.

Using all these conventions we can write a simple python script 
``build_ssc_pedigree.py``
to convert
``SupplementaryData1_Children.tsv`` into a pedigree file ``ssc_denovo.ped``:

.. code-block:: python

    """Converts SupplementaryData1_Children.tsv into a pedigree file."""
    import pandas as pd
    
    children = pd.read_csv("SupplementaryData1_Children.tsv", sep="\t")
    ssc = children[children.collection == "SSC"]
    
    # list of all individuals in SSC
    persons = []
    # each person is represented by a tuple:
    # (familyId, personId, dadId, momId, status, sex)
    
    for fam_id, members in ssc.groupby("familyId"):
        persons.append((fam_id, f"{fam_id}.mo", "0", "0", "unaffected", "F"))
        persons.append((fam_id, f"{fam_id}.fa", "0", "0", "unaffected", "F"))
        for child in members.to_dict(orient="records"):
            persons.append((
                fam_id, child["personId"], f"{fam_id}.fa", f"{fam_id}.mo",
                child["affected status"], child["sex"]))
    
    with open("ssc_denovo.ped", "wt", encoding="utf8") as output:
        output.write(
            "\t".join(("familyId", "personId", "dadId", "momId", "status", "sex")))
        output.write("\n")
    
        for person in persons:
            output.write("\t".join(person))
            output.write("\n")

If we run this script it will read ``SupplementaryData1_Children.tsv`` and
produce the appropriate pedigree file ``ssc_denovo.ped``.

Preprocess the variants data
____________________________

The ``SupplementaryData2_SSC.tsv`` file contains 255231 variants. To import so
many variants in in-memory genotype storage is not appropriate. For this
example we are going to use a subset of 10000 variants:

.. code-block:: bash

    head -n 10001 SupplementaryData2_SSC.tsv > ssc_denovo.tsv


Data import of ``ssc_denovo``
_____________________________

Now we have a pedigree file ``ssc_denovo.ped`` and a list of de novo
variants ``ssc_denovo.tsv``. Let us prepare an import project configuration
file ``ssc_denovo.yaml``:

.. code-block:: yaml

    id: ssc_denovo
    
    input:
      pedigree:
        file: ssc_denovo.ped
    
      denovo:
        files:
          - ssc_denovo.tsv
        person_id: personIds
        variant: variant
        location: location


To import the study we should run:

.. code-block:: bash

    import_tools ssc_denovo.yaml

and when the import finishes we can run the development GPF server:

.. code-block:: bash

    wgpf run

In the list of studies, we should have a new study ``ssc_denovo``.



Getting started with Dataset Statistics
##########################################

.. _reports_tool:


To generate family and de novo variant reports, you can use
the ``generate_common_report.py`` tool. It supports the option ``--show-studies``
to list all studies and datasets configured in the GPF instance:

.. code-block:: bash

    generate_common_report.py --show-studies

To generate the reports for a given study or dataset, you can use the 
``--studies`` option. 

By default the dataset statistics are disabled. If we try to run

.. code-block:: bash

    generate_common_report.py --studies helloworld

it will not generate the dataset statistics. Instead, it will print 
a message that the reports are disabled to study ``helloworld``:

.. code-block:: bash

    WARNING:generate_common_reports:skipping study helloworld 

To enable the dataset statistics for the ``helloworld`` dataset we need to
modify the configuration and add
a new section that enables dataset statistics:

.. code-block:: yaml

  id: helloworld
  name: Hello World Dataset
  
  studies:
    - denovo_helloworld
    - vcf_helloworld
  
  common_report:
    enabled: True

Let us now re-run the ``generate_common_report.py`` command:

.. code-block:: bash

    generate_common_report.py --studies helloworld

If we now start the GPF development server:

.. code-block:: bash

    wgpf run

and browse the ``helloworld`` dataset we will see the `Dataset Statistics`
section available.


Getting started with de novo gene sets
######################################

To generate de novo gene sets, you can use the
``generate_denovo_gene_sets.py`` tool. Similar to :ref:`reports_tool` above,
you can use the ``--show-studies`` and ``--studies`` option.

By default the de novo gene sets are disabled. If you want to enable them for a 
specific study or dataset you need to update the configuration and add a section
that enable the de novo gene sets:

.. code-block:: yaml

    denovo_gene_sets:
      enabled: true

For example the configuration of ``helloworld`` dataset should become similar to:

.. code-block:: yaml

    id: helloworld
    name: Hello World Dataset
    
    studies:
      - denovo_helloworld
      - vcf_helloworld
    
    common_report:
      enabled: True
    
    denovo_gene_sets:
      enabled: true
    

Then we can generate the de novo gene sets for ``helloworld`` dataset by
running:

.. code-block:: bash

    generate_denovo_gene_sets.py --studies helloworld


.. include:: getting_started/getting_started_with_annotation.rst

.. include:: getting_started/getting_started_with_preview_columns.rst

.. include:: getting_started/getting_started_with_gene_browser.rst

.. todo::

    WIP


.. include:: getting_started/getting_started_with_enrichment.rst

.. include:: getting_started/getting_started_with_phenotype_data.rst




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
