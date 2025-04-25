.. _example_denovo_import:

Example import of real de Novo variants
#######################################

Source of the data
++++++++++++++++++

As an example, let us import de novo variants from the following paper:
`Yoon, S., et al. Rates of contributory de novo
mutation in high and low-risk autism families.
Commun Biol 4, 1026 (2021). <https://doi.org/10.1038/s42003-021-02533-z>`_

We will focus on de novo variants from the SSC collection published in the
aforementioned paper.

To import these variants into the GPF system, we need
a pedigree file describing the families and
a list of de novo variants.

From the supplementary data for the paper can download the following files:

* The list
  of sequenced children available from
  `Supplementary Data
  1. <https://pmc.ncbi.nlm.nih.gov/articles/instance/8410909/bin/42003_2021_2533_MOESM3_ESM.xlsx>`_

* The list of SNP and INDEL de novo variants is available from
  `Supplementary Data
  2. <https://pmc.ncbi.nlm.nih.gov/articles/instance/8410909/bin/42003_2021_2533_MOESM4_ESM.xlsx>`_


.. note::

    All the data files needed for this example are available in the
    `gpf-getting-started <https://github.com/iossifovlab/gpf-getting-started.git>`_
    repository under the subdirectory ``example_imports/denovo_and_cnv_import``.


.. _example_denovo_pedigree:

Preprocess the Family Data
++++++++++++++++++++++++++

The list of children in ``Supplementary_Data_1.tsv.gz`` contains a lot of data
that is not relevant for the import.
We are going to use only the first five
columns from that file that look as follows:

.. code-block:: bash

    gunzip -c Supplementary_Data_1.tsv.gz | head | cut -f 1-5 | less -S -x 20


    collection          familyId            personId            affected status     sex
    SSC                 11000               11000.p1            affected            M
    SSC                 11000               11000.s1            unaffected          F
    SSC                 11003               11003.p1            affected            M
    SSC                 11003               11003.s1            unaffected          F
    SSC                 11004               11004.p1            affected            M
    SSC                 11004               11004.s1            unaffected          M
    SSC                 11006               11006.p1            affected            M
    SSC                 11006               11006.s1            unaffected          M
    SSC                 11008               11008.p1            affected            M


* The first column contains the collection. This study contains data from SSC
  and AGRE collections. We are going to import only variants from the
  SSC collection.

* The second column contains the family ID.

* The third column contains the person's ID.

* The fourth column contains the affected status of the individual.

* The fifth column contains the sex of the individual.

We need a pedigree file describing the family's structure to import the data
into GPF. The `SupplementaryData1_Children.tsv.gz` contains only the  children;
it does not include information about their parents.
Fortunately for the SSC collection, it is not difficult to build the whole
families' structures from the information we have.

So, before starting the work on the import, we need to preprocess the
list of children and transform it into a pedigree file.

For the SSC collection, if you have a family with ID`<fam_id>`, then the
identifiers of the individuals in the family are going to be formed as follows:

* mother - ``<fam_id>.mo``;

* father - ``<fam_id>.fa``;

* proband - ``<fam_id>.p1``;

* first sibling - ``<fam_id>.s1``;

* second sibling - ``<fam_id>.s2``.

Another essential restriction for SSC is that the only affected person in the
family is the proband. The affected status of the mother, father, and
siblings is unaffected.

Having this information, we can use the following `Awk` script to transform
the list of children in a pedigree:

.. code-block:: bash

    gunzip -c Supplementary_Data_1.tsv.gz | awk '
        BEGIN {
            OFS="\t"
            print "familyId", "personId", "dadId", "momId", "status", "sex"
        }
        $1 == "SSC" {
            fid = $2
            if( fid in families == 0) {
                families[fid] = 1
                print fid, fid".mo", "0", "0", "unaffected", "F"
                print fid, fid".fa", "0", "0", "unaffected", "M"
            }
            print fid, $3, fid".fa", fid".mo", $4, $5
        }' > ssc_denovo.ped


If we run this script, it will read ``Supplementary_Data_1.tsv.gz`` and produce
the appropriate pedigree file ``ssc_denovo.ped``.

.. note::
    The resulting pedigree file is also available in the
    `gpf-getting-started <https://github.com/iossifovlab/gpf-getting-started.git>`_
    repository under the subdirectory
    ``example_imports/denovo_and_cnv_import``.

Here is a fragment from the resulting pedigree file:

.. literalinclude:: gpf-getting-started/example_imports/denovo_and_cnv_import/ssc_denovo.ped
    :tab-width: 15
    :lines: 1-11

Preprocess the SNP and INDEL de Novo variants
+++++++++++++++++++++++++++++++++++++++++++++

The `Supplementary_Data_2.tsv.gz` file contains 255232 variants.
For the import, we will use columns four and nine from this file:

.. code-block:: bash

    gunzip -c Supplementary_Data_2.tsv.gz | head | cut -f 4,9 | less -S -x 20

    personIds           variant in VCF format
    13210.p1            chr1:184268:G:A
    12782.s1            chr1:191408:G:A
    12972.s1            chr1:271774:AG:A
    12420.p1            chr1:484721:AG:A
    12518.p1,12518.s1   chr1:691130:T:C
    13882.p1            chr1:738645:C:G
    14039.s1            chr1:819832:G:T
    13872.p1            chr1:824001:AAAAT:A


Using the following `Awk` script, we can transform this file into easy to
import the list of de Novo variants:

.. code-block:: bash

    gunzip -c Supplementary_Data_2.tsv.gz | cut -f 4,9 | awk '
        BEGIN{
            OFS="\t"
            print "chrom", "pos", "ref", "alt", "person_id"
        }
        NR > 1 {
            split($2, v, ":")
            print v[1], v[2], v[3], v[4], $1
        }' > ssc_denovo.tsv


This script will produce a file named ``ssc_denovo.tsv`` with the following
content:

.. literalinclude:: gpf-getting-started/example_imports/denovo_and_cnv_import/ssc_denovo.tsv
    :tab-width: 15
    :lines: 1-11

.. note::
    The resulting ``ssc_denovo.tsv`` file is also available in the
    `gpf-getting-started <https://github.com/iossifovlab/gpf-getting-started.git>`_
    repository under the subdirectory
    ``example_imports/denovo_and_cnv_import/input_data``.



Caching GRR
+++++++++++

Now we are about to import 255K variants. During the import, the GPF system
will annotate these variants using the GRR resources from our
`public GRR. <https://grr.iossifovlab.com>`_
For small studies with few variants, this approach is quite convenient.
However, for larger studies, it is better to cache the GRR resources locally.

To do this, we need to configure the GRR to use a local cache. Create a file
named ``.grr_definition.yaml`` in your home directory with the following
content:

.. code-block:: yaml

    id: "seqpipe"
    type: "url"
    url: "https://grr.iossifovlab.com"
    cache_dir: "<path_to_your_cache_dir>"

The ``cache_dir`` parameter specifies the directory where the GRR resources
will be cached. The cache directory should be specified as an absolute path.
For example,  ``/tmp/grr_cache`` or ``/Users/lubo/grrCache``.

To download all the resources needed for our ``minimal_instance`` annotation,
run the following command from the ``gpf-getting-started`` directory:

.. code-block:: bash

    grr_cache_repo -i minimal_instance/gpf_instance.yaml

.. note::

    The ``grr_cache_repo`` command will download all the resources needed for
    the GPF instance. This may take a while, depending on your internet
    connection and the number of resources your configuration requires.

    The resources will be downloaded to the directory specified in the
    ``cache_dir`` parameter in the ``.grr_definition.yaml`` file.

    For the ``gpf-getting-started`` repository, the resources that will be
    downloaded are:

    * ``hg38/genomes/GRCh38-hg38``

    * ``hg38/gene_models/MANE/1.3``

    * ``hg38/variant_frequencies/gnomAD_4.1.0/genomes/ALL``

    * ``hg38/scores/ClinVar_20240730``

    The total size of the downloaded resources is about 15 GB.


Data Import of ``ssc_denovo``
+++++++++++++++++++++++++++++

Now we have a pedigree file, ``ssc_denovo.ped``, and a list of de novo
variants, ``ssc_denovo.tsv``. Let us prepare an import project configuration
file, ``ssc_denovo.yaml``:

.. literalinclude:: gpf-getting-started/example_imports/denovo_and_cnv_import/ssc_denovo.yaml
    :linenos:
    :emphasize-lines: 11-12

When importing genotype data, we often need to instruct the import tool how to
split the import process into multiple jobs. For this purpose, we can use
``processing_config`` section of the import project. On lines 11-12 of the
``ssc_denovo.yaml`` file, we have defined the ``processing_config`` section
that will split the import de Novo variants into jobs by chromosome. (For more
on import project configuration, see :doc:`import_tool`.)


.. note::

    The project file ``ssc_denovo.yaml`` is available in the the ``gpf-getting-started``
    repository under the subdirectory
    ``example_imports/denovo_and_cnv_import``.

To import the study, from the ``gpf-getting-started`` directory we should run:

.. code-block:: bash

    time import_genotypes -v -j 10 example_imports/denovo_and_cnv_import/ssc_denovo.yaml

This command will take a while to run. The time it takes to run will depend on
the number of variants in the input file and the number of threads used for
the import. For example, on a machine with 10 threads, the import of the SSC
de Novo variants took about 5 minutes to run:

.. code-block:: bash

    real    5m29.950s
    user    31m52.320s
    sys     1m41.755s

The ``-j 10`` option instructs the ``import_genotypes`` tool to use 10 threads
and the ``-v`` option controls the verbosity of the output.

When the import finishes, we can run the development GPF server:


.. code-block:: bash

    wgpf run

In the `Home` page of the GPF instance, we should have the new study
``ssc_denovo``.

.. figure:: getting_started_files/ssc_denovo_home_page.png

    Home page with the imported SSC de Novo variants.

If you follow the link to the study and choose the `Genotype Browser` tab, you
will be able to query the imported variants.

.. figure:: getting_started_files/ssc_denovo_genotype_browser.png

    Genotype browser for the SSC de novo variants.


Configure preview and download columns
++++++++++++++++++++++++++++++++++++++

While importing the SSC de novo variants, we were using the annotation defined
in the minimal instance configuration file. So, all imported variants are
annotated with GnomAD and ClinVar genomic scores.

We can use these score values to define additional columns in the preview
table and the download file similar to
:ref:`getting_started_with_preview_columns`.

Edit the ``ssc_denovo`` configuration file located at
``minimal_instance/studies/ssc_denovo/ssc_denovo.yaml`` and add the following
snippet to the configuration file:

.. code-block:: yaml
    :linenos:

    genotype_browser:
      columns:
        genotype:
          gnomad_v4_genome_af:
            name: gnomAD v4 AF
            source: gnomad_v4_genome_ALL_af
            format: "%%.5f"
          clinvar_clnsig:
            name: CLNSIG
            source: CLNSIG
          clinvar_clndn:
            name: CLNDN
            source: CLNDN

      column_groups:
        gnomad_v4:
          name: gnomAD v4
          columns:
          - gnomad_v4_genome_af

        clinvar:
          name: ClinVar
          columns:
          - clinvar_clnsig
          - clinvar_clndn

      preview_columns_ext:
        - gnomad_v4
        - clinvar

      download_columns_ext:
        - gnomad_v4_genome_af
        - clinvar_clnsig
        - clinvar_clndn

Now, restart the GPF development server:

.. code:: bash

    wgpf run


Go to the `Genotype Browser` tab of the ``ssc_denovo`` study and click
`Preview Table` button. The preview table should now contain the additional
columns for `GnomAD` and `ClinVar` genomic scores.

.. figure:: getting_started_files/ssc_denovo_genotype_browser_with_annotated_columns.png

    Genotype browser with additional columns for GnomAD and ClinVar genomic scores.
