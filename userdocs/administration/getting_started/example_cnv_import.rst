.. _example_cnv_import:

Example import of real CNV variants
###################################
  
Source of the data
++++++++++++++++++

As an example for import of CNV variants we will use data from the following 
paper:
`Yoon, S., et al. Rates of contributory de novo 
mutation in high and low-risk autism families. 
Commun Biol 4, 1026 (2021). <https://doi.org/10.1038/s42003-021-02533-z>`_

We already discussed the import of de Novo variants from this paper in 
:ref:`example_denovo_import`.

Now we will focus on the import of CNV variants from the same paper.

To import these variants into the GPF system, we need 
a pedigree file describing the families and 
a list of CNV variants.

From the supplementary data for the paper can download the following files:

* The list 
  of sequenced children available from 
  `Supplementary Data 
  1. <https://pmc.ncbi.nlm.nih.gov/articles/instance/8410909/bin/42003_2021_2533_MOESM3_ESM.xlsx>`_

* The list of CNV de novo variants is available from
  `Supplementary Data 
  1. <https://pmc.ncbi.nlm.nih.gov/articles/instance/8410909/bin/42003_2021_2533_MOESM6_ESM.xlsx>`_

.. note:: 

    All the data files needed for this example are available in the
    `gpf-getting-started <https://github.com/iossifovlab/gpf-getting-started.git>`_
    repository under the subdirectory ``example_imports/denovo_and_cnv_import``.

We already discussed how to transform the list of children into a pedigree file
in the :ref:`example_denovo_pedigree` section.

Now we need to prepare the CNV variants file.

Preprocess the CNV variants
+++++++++++++++++++++++++++

The `Supplementary_Data_4.tsv.gz` file contains 376 CNV variants from SSC and 
AGRE collections.

For the import we will use the colums two, five, six and seven:

.. code-block:: bash

    gunzip -c Supplementary_Data_4.tsv.gz | cut -f 2,5-7 | less -S -x 25

    collection               personIds                location                 variant
    SSC                      12613.p1                 chr1:1305145-1314126     duplication
    AGRE                     AU2725301                chr1:3069177-4783791     duplication
    SSC                      13424.s1                 chr1:3975501-3977800     deletion
    SSC                      12852.p1                 chr1:6647401-6650500     deletion
    SSC                      13776.p1                 chr1:8652301-8657600     deletion
    SSC                      13373.s1                 chr1:9992001-9994100     deletion
    SSC                      14198.p1                 chr1:12224601-12227300   deletion
    SSC                      13259.p1                 chr1:15687701-15696200   deletion
    SSC                      14696.s1                 chr1:30388501-30398807   deletion

Using the following `Awk` script we will filter only variants from SSC collection:

.. code-block:: bash

    gunzip -c Supplementary_Data_4.tsv.gz | cut -f 2,5-7 | awk '
        BEGIN{
            OFS="\t"
            print "location", "variant", "person_id"
        }
        $1 == "SSC" {
            print $3, $4, $2
        }' > ssc_cnv.tsv

This script will produce a file named ``ssc_cnv.tsv`` with the following content:

.. literalinclude:: gpf-getting-started/example_imports/denovo_and_cnv_import/ssc_cnv.tsv     
    :tab-width: 30
    :lines: 1-11

.. note::
    The resulting ``ssc_cnv.tsv`` file is available in the 
    `gpf-getting-started <https://github.com/iossifovlab/gpf-getting-started.git>`_
    repository under the subdirectory 
    ``example_imports/denovo_and_cnv_import/input_data``.


Data Import of ``ssc_cnv``
++++++++++++++++++++++++++

Now we have a pedigree file, ``ssc_denovo.ped``, and a list of de novo 
variants, ``ssc_cnv.tsv``. Let us prepare an import project configuration 
file, ``ssc_cnv.yaml``:

.. literalinclude:: gpf-getting-started/example_imports/denovo_and_cnv_import/ssc_cnv.yaml
    :linenos:
    :emphasize-lines: 12-14

Lines 12-14 define how CNV variant is defined in the input file. The ``variant``
specifies the type of the variant and values ``deletion`` and ``duplication`` are
used to define the CNV variant type.

.. note::

    The project file ``ssc_cnv.yaml`` is available in the the ``gpf-getting-started``
    repository under the subdirectory 
    ``example_imports/denovo_and_cnv_import``.

To import the study, from the ``gpf-getting-started`` directory we should run:

.. code:: bash

    time import_genotypes -v -j 1 example_imports/denovo_and_cnv_import/ssc_cnv.yaml

When the import finishes, we can run the development GPF server:


.. code:: bash

    wgpf run

In the `Home` page of the GPF instance we should have the new study ``ssc_cnv``.

.. figure:: getting_started_files/ssc_cnv_home_page.png

    Home page with the imported ``ssc_cnv`` study.

If you follow the link to the study, and choose the `Genotype Browser` tab, you 
will be able to query the imported CNV variants.

.. figure:: getting_started_files/ssc_cnv_genotype_browser.png

    Genotype browser for the SSC CNV variants.
