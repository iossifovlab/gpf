Example import of real phenotype data
#####################################

Source of the data
++++++++++++++++++

As an example, let us import phenotype data from the following paper:
`Iossifov, I., O'Roak, B., Sanders, S. et al. The contribution of de novo
coding mutations to autism spectrum disorder. Nature 515, 216-221 (2014).
<https://doi.org/10.1038/nature13908>`_

We will focus on the phenotype data available from the paper.

To import the phenotype data into the GPF system, we need
a pedigree file describing the families and
instrument files with phenotype measures.

Information about the families and the phenotype measures is available in
the Supplementary Table 1 of the paper.

All supplementary data files are available from the
`Nature website
<https://static-content.springer.com/esm/art%3A10.1038%2Fnature13908/MediaObjects/41586_2014_BFnature13908_MOESM117_ESM.zip>`_


.. note::

    All the data needed for this example are available in the
    `gpf-getting-started <https://github.com/iossifovlab/gpf-getting-started.git>`_
    repository under the subdirectory ``example_imports/pheno_import``.


Preprocess the Family Data
++++++++++++++++++++++++++

The list of children in ``Supplementary_Table_1.tsv.gz`` contains both
descriptions of families, phenotype measures, and some other information,
that we do not need for the import.

We will construct the pedigree file from the first four columns of the
``Supplementary_Table_1.tsv.gz`` file. 

.. code-block:: bash

    gunzip -c example_imports/pheno_import/Supplementary_Table_1.tsv.gz | \
        head | cut -f 1-4 | less -S -x 20


.. code-block:: text

    familyId            collection          probandGender       siblingGender
    11542               ssc                 F                   F
    13736               ssc                 M                   M
    13735               ssc                 M                   F
    13734               sac                 F                   M
    11546               ssc                 M                   M
    11547               ssc                 M                   
    13731               ssc                 M                   
    11545               ssc                 M                   
    11549               ssc                 M                   F


The procedure will be similar to one
already described in :ref:`example_denovo_pedigree` and will rely on the
specific structure of the families in the SSC collection described there.

An example Awk script to transform the Supplementary Table 1 into a pedigree
file is given below.

.. code-block:: bash

    gunzip -c example_imports/pheno_import/Supplementary_Table_1.tsv.gz | cut -f 1-4 | awk '
        BEGIN {
            OFS="\t"
            print "familyId", "personId", "dadId", "momId", "status", "sex"
        }
        $2 == "ssc" {
            fid = $1
            if( fid in families == 0) {
                families[fid] = 1
                print fid, fid".mo", "0", "0", "unaffected", "F"
                print fid, fid".fa", "0", "0", "unaffected", "M"
                print fid, fid".p1", fid".fa", fid".mo", "affected", $3
                if ($4 != "") {
                    print fid, fid".s2", fid".fa", fid".mo", "unaffected", $4
                }
            }
        }' > example_imports/pheno_import/ssc_pheno.ped

If we run this script, it will read ``Supplementary_Table_1.tsv.gz`` and produce
the appropriate pedigree file ``ssc_pheno.ped``.

.. note::
    The resulting pedigree file is also available in the
    `gpf-getting-started <https://github.com/iossifovlab/gpf-getting-started.git>`_
    repository under the subdirectory
    ``example_imports/pheno_import``.

Here is a fragment from the resulting pedigree file:

.. literalinclude:: gpf-getting-started/example_imports/pheno_import/ssc_pheno.ped
    :tab-width: 15
    :lines: 1-11

Preprocess the available phenotype measures
+++++++++++++++++++++++++++++++++++++++++++

The `Supplementary_Table_1.tsv.gz` file contains some phenotype measures
that we will use for the import. We will focus on the columns 1 and 8-13
of the file.

.. code-block:: bash

    gunzip -c example_imports/pheno_import/Supplementary_Table_1.tsv.gz | \
        head | cut -f 1,8-13 | less -S -x 35

.. code-block:: text

    familyId                           motherRace                         fatherRace                         probandVIQ                         probandNVIQ                        motherAgeInMonthsAtBirthOfProband  fatherAgeInMonthsAtBirthOfProband
    11542                              more-than-one-race                 white                              121                                102                                429                                430
    13736                              white                              white                              119                                112                                396                                400
    13735                              asian                              asian                              30                                 27                                 386                                463
    13734                              white                              white                              36                                 51                                 368                                348
    11546                              white                              white                              100                                123                                437                                406
    11547                              asian                              asian                              49                                 49                                 380                                434
    13731                              white                              white                              115                                113                                367                                491
    11545                              white                              white                              83                                 114                                383                                441
    11549                              african-amer                       african-amer                       36                                 61                                 406                                481

The available measures are as follows:

- ``motherRace``: mother's race.
- ``fatherRace``: father's race.
- ``probandVIQ``: proband's verbal IQ.
- ``probandNVIQ``: proband's non-verbal IQ.
- ``motherAgeInMonthsAtBirthOfProband``: mother's age in months at the birth of
  the proband.
- ``fatherAgeInMonthsAtBirthOfProband``: father's age in months at the birth of
  the proband.

Using the following Awk script we will extract the relevant measures into
an instrument file.

.. code-block:: bash

    gunzip -c example_imports/pheno_import/Supplementary_Table_1.tsv.gz | cut -f 1,8-13 | awk '
        BEGIN {
            OFS=","
            print "individual", "motherRace", "fatherRace", "probandVIQ", "probandNVIQ", "motherAgeInMonthsAtBirthOfProband", "fatherAgeInMonthsAtBirthOfProband"
        }
        $1 != "familyId" {
            print $1".p1", $2, $3, $4, $5, $6, $7, $8
        }' > example_imports/pheno_import/proband_measures.csv


This script will produce a file named ``proband_measures.csv`` with the following
content:

.. csv-table:: ``example_imports/pheno_import/proband_measures.csv``
    :header-rows: 1

    individual,motherRace,fatherRace,probandVIQ,probandNVIQ,motherAgeInMonthsAtBirthOfProband,fatherAgeInMonthsAtBirthOfProband
    11542.p1,more-than-one-race,white,121,102,429,430,
    13736.p1,white,white,119,112,396,400,
    13735.p1,asian,asian,30,27,386,463,
    13734.p1,white,white,36,51,368,348,
    11546.p1,white,white,100,123,437,406,
    11547.p1,asian,asian,49,49,380,434,
    13731.p1,white,white,115,113,367,491,
    11545.p1,white,white,83,114,383,441,
    11549.p1,african-amer,african-amer,36,61,406,481,
    13739.p1,white,white,16,35,464,467,

.. note::
    The resulting file ``proband_measures.csv`` is also available in the
    `gpf-getting-started <https://github.com/iossifovlab/gpf-getting-started.git>`_
    repository under the subdirectory
    ``example_imports/pheno_import``.


Data Import of ``ssc_pheno``
+++++++++++++++++++++++++++++

Now we have a pedigree file, ``ssc_pheno.ped``, and an instrument file
``proband_measures.csv``. To import this data we need an import
project.  A suitable import project is already available in the example imports
directory ``example_imports/pheno_import/ssc_pheno.yaml``:

.. literalinclude:: gpf-getting-started/example_imports/pheno_import/ssc_pheno.yaml
    :linenos:

To import the phenotype data we will use the ``import_phenotypes`` tool.

.. code-block:: bash

    import_phenotypes example_imports/pheno_import/ssc_pheno.yaml

When the import finishes, we can run the GPF development server using:

.. code-block:: bash

    wgpf run

Now, on the GPF instance `Home Page`, you should see the ``ssc_pheno`` phenotype
study. If you follow the link, you will see the `Phenotype Browser` tab with the
imported data.

.. figure:: getting_started_files/ssc_pheno_phenotype_browser.png

    Phenotype Browser with imported phenotype study ``ssc_pheno``


Configure a genotype study ``ssc_denovo`` to use phenotype data
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Now we can configute the ``ssc_denovo`` genotype study to use the newly
import phenotype data. We need to edit the ``ssc_denovo.yaml`` configuration
file located in the ``minimal_instance/studies/ssc_denovo/`` directory and
add the line 18 as shown below:


.. code-block:: yaml
    :linenos:
    :emphasize-lines: 18

    id: ssc_denovo
    conf_dir: .
    has_denovo: true
    has_cnv: false
    has_transmitted: false
    genotype_storage:
      id: internal
      tables:
        pedigree: parquet_scan('ssc_denovo/pedigree/pedigree.parquet')
        meta: parquet_scan('ssc_denovo/meta/meta.parquet')
        summary: parquet_scan('ssc_denovo/summary/*.parquet')
        family: parquet_scan('ssc_denovo/family/*.parquet')
    genotype_browser:
      enabled: true
    denovo_gene_sets:
      enabled: true

    phenotype_data: ssc_pheno

When you restart the GPF instance, showld be able to see `Phenotype Browser`
and the `Phenotype Tool` tabs enable for the study ``ssc_denovo``.

.. figure:: getting_started_files/ssc_denovo_with_ssc_pheno_configured.png

    Genotype study ``ssc_denovo`` with phenotype data configured.

Now we can use the `Phenotype Tool` to see how de Novo variants are corelated
with the proband's phenotype measures. 

.. figure:: getting_started_files/ssc_denovo_phenotype_tool.png

    Phenotype Tool results for the proband non-verbal IQ in ``ssc_denovo`` study.
