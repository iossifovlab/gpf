GPF Getting Started Guide
=========================

Prerequisites
#############

This guide assumes that you are working on a recent Linux box.

Working version of anaconda or miniconda
++++++++++++++++++++++++++++++++++++++++

The GPF system is distributed as an Anaconda package using the ``conda``
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
        -c conda-forge \
        -c bioconda \
        -c iossifovlab \
        -c defaults \
        gpf_wdae

This command is going to install GPF and all of its dependencies.

Clone the example "getting-started" repository
++++++++++++++++++++++++++++++++++++++++++++++

.. code-block:: bash

    git clone https://github.com/iossifovlab/getting-started.git

This repository provides a minimal instance and sample data to be imported.

The reference genome used by this GPF instance is ``hg38/genomes/GRCh38-hg38`` from the default GRR.
The gene models used by this GPF instance are ``hg38/gene_models/refSeq_v20200330`` from the default GRR.
If not specified otherwise, GPF uses the default genomic resources
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

Additionally, GPF will also consider the ``DAE_DB_DIR`` environment variable.
Sourcing the provided ``setenv.sh`` file will set this variable for you.

.. code-block:: bash

    source setenv.sh

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

Let us import a small list of de novo variants. We will need the list of
de novo variants ``raw_genotype_data/helloworld.tsv``, and a pedigree file
that describes the families - ``raw_genotype_data/helloworld.ped``:

A project configuration file for importing this study
(``raw_genotype_data/import_denovo_project.yaml``) is also provided.

To import this project run the following command:

.. code-block:: bash

    import_genotypes raw_genotype_data/import_denovo_project.yaml

When the import finishes you can run the GPF development server using:

.. code-block:: bash

    wgpf run

and browse the content of the GPF development server at ``http://localhost:8000``

Example import of VCF variants: ``vcf_helloworld``
++++++++++++++++++++++++++++++++++++++++++++++++++

Similar to the sample denovo variants, there are also sample variants in VCF format.
They can be found in ``raw_genotype_data/helloworld.vcf`` and the same pedigree file from before is used.

To import them, run the following command:

.. code-block:: bash

    import_genotypes raw_genotype_data/vcf_helloworld.yaml

When the import finishes you can run the GPF development server using:

.. code-block:: bash

    wgpf run

and browse the content of the GPF development server at ``http://localhost:8000``

Example of a dataset (group of genotype studies)
++++++++++++++++++++++++++++++++++++++++++++++++

The already imported studies ``denovo_helloworld`` and ``vcf_helloworld``
have genomic variants for the same group of individuals ``helloworld.ped``.
We can create a dataset (group of genotype studies) that include both studies.

To this end create a directory ``datasets/helloworld`` inside the GPF instance
directory ``minimal_instance``:

.. code-block:: bash

    cd minimal_instance
    mkdir -p datasets/helloworld

and place the following configuration file ``helloworld.yaml`` inside that directory:

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
``generate_denovo_gene_sets.py`` tool. Similar to the `reports_tool`_ above,
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

.. include:: getting_started/getting_started_with_enrichment.rst

.. include:: getting_started/getting_started_with_phenotype_data.rst

Example Usage of GPF Python Interface
#####################################

The simplest way to start using GPF's Python API is to import the ``GPFInstance``
class and instantiate it:

.. code-block:: python3

    from dae.gpf_instance.gpf_instance import GPFInstance
    gpf_instance = GPFInstance.build()

This ``gpf_instance`` object groups together a number of objects, each dedicated
to managing different parts of the underlying data. It can be used to interact
with the system as a whole.

For example, to list all studies configured in the startup GPF instance, use:

.. code-block:: python3

    gpf_instance.get_genotype_data_ids()

This will return a list with the ids of all configured studies:

.. code-block:: python3

    ['denovo_helloworld',
     'vcf_helloworld',
     'helloworld']

To get a specific study and query it, you can use:

.. code-block:: python3

    st = gpf_instance.get_genotype_data('helloworld')
    vs = list(st.query_variants())

.. note::
    The ``query_variants`` method returns a Python iterator.

To get the basic information about variants found by the ``query_variants`` method,
you can use:

.. code-block:: python3

    for v in vs:
        for aa in v.alt_alleles:
            print(aa)

    chr1:1287138 C->A f1
    chr1:3602485 AC->A f1
    chr1:12115730 G->A f1
    chr1:20639952 C->T f2
    chr1:21257524 C->T f2
    chr14:21385738 C->T f1
    chr14:21385738 C->T f2
    chr14:21385954 A->C f2
    chr14:21393173 T->C f1
    chr14:21393702 C->T f2
    chr14:21393860 G->A f1
    chr14:21403023 G->A f1
    chr14:21403023 G->A f2
    chr14:21405222 T->C f2
    chr14:21409888 T->C f1
    chr14:21409888 T->C f2
    chr14:21429019 C->T f1
    chr14:21429019 C->T f2
    chr14:21431306 G->A f1
    chr14:21431623 A->C f2
    chr14:21393540 GGAA->G f1

The ``query_variants`` interface allows you to specify what kind of variants
you are interested in. For example, if you only need "splice-site" variants, you
can use:

.. code-block:: python3

    st = gpf_instance.get_genotype_data('helloworld')
    vs = st.query_variants(effect_types=['splice-site'])
    vs = list(vs)
    print(len(vs))

    >> 2

Or, if you are interested in "splice-site" variants only in people with
"prb" role, you can use:

.. code-block:: python3

    vs = st.query_variants(effect_types=['splice-site'], roles='prb')
    vs = list(vs)
    len(vs)

    >> 1
