Working With VCF Files Guide
============================


Import data from the "1000 Genome Project"
##########################################

The data used in this guide is from the "1000 Genome Project".
For more information, visit `IGSR <https://www.internationalgenome.org/about>`_.

Begin by making a new directory, in which you can download and create files:

.. code-block:: bash

    mkdir 1KGP

Navigate to it:

.. code-block:: bash

    cd 1KGP

Download the data:

.. code-block:: bash

    wget ftp://ftp-trace.ncbi.nih.gov/1000genomes/ftp/release/20130502/ALL.chr1.phase3_shapeit2_mvncall_integrated_v5a.20130502.genotypes.vcf.gz
    wget ftp://ftp-trace.ncbi.nih.gov/1000genomes/ftp/release/20130502/supporting/related_samples_vcf/ALL.chr1.phase3_shapeit2_mvncall_integrated_v5_related_samples.20130502.genotypes.vcf.gz
    wget ftp://ftp-trace.ncbi.nih.gov/1000genomes/ftp/technical/working/20130606_sample_info/20130606_sample_info.xlsx

The three downloaded files are:

* ``ALL.chr1.phase3_shapeit2_mvncall_integrated_v5a.20130502.genotypes.vcf.gz`` - contains the variants data of the individuals

* ``ALL.chr1.phase3_shapeit2_mvncall_integrated_v5_related_samples.20130502.genotypes.vcf.gz`` - contains the variants data of the related individuals

* ``20130606_sample_info.xlsx`` - contains information about all the examined individuals


Creating the pedigree file
##########################

Information about the individual's relationships within their family can be found
in the spreadsheet file ``20130606_sample_info.xlsx``, in the 'Sample Info' tab.
Let's create a pedigree file for the family with id "PR05". For more information
on working with pedigree files, refer to the
:ref:`Working With Pedigrees Guide <working_with_pedigrees>`.

First, create the pedigree file:

.. code-block:: bash

    touch PR05.ped

Then open it in a text editor and add the necessary columns - familyId,
personId, momId, dadId, sex, status and role. Fill in the individuals and
the values in each column, by referring to the spreadshee's information.
After the editing, the pedigree file should look like this:

.. code-block::

    familyId	personId	momId	dadId	sex	status	role
    PR05	HG00731	0	0	M	unspecified	dad
    PR05	HG00732	0	0	F	unspecified	mom
    PR05	HG00733	HG00732	HG00731	M	unspecified	prb


.. warning::
    The columns should be separated by tabs, not spaces.


Next, you have to standardize the pedigree file, using the ``ped2ped.py`` tool::

    ped2ped.py PR05.ped -o PR05_standardized.ped --ped-layout-mode generate

This command will generate a new pedigree file - ``PR05_standardized.ped`` with
two newly added columns - sampleId and layout, which will be used
by the GPF system. Now the pedigree file is ready for importing.


Creating the VCF files
######################

To extract the variant data for the individuals
`HG00731`, `HG00732` and `HG00733` in a separate files, we will
use `Bcftools <https://samtools.github.io/bcftools/>`_.

Let's start with individual `HG00733`, whose data is in the
``ALL.chr1.phase3_shapeit2_mvncall_integrated_v5_related_samples.20130502.genotypes.vcf.gz`` file.
Using bcftools' view ``--samples`` argument, we can get the data for a specific individual.
Adding `> HG00733.vcf` in the end of the command will redirect the command's result
into a new file, named ``HG00733.vcf``::

    bcftools view \
    --samples HG00733 \
    ALL.chr1.phase3_shapeit2_mvncall_integrated_v5_related_samples.20130502.genotypes.vcf.gz \
    > HG00733.vcf

The data for individuals `HG00731` and `HG00732` is in the second vcf file -
``ALL.chr1.phase3_shapeit2_mvncall_integrated_v5a.20130502.genotypes.vcf.gz``.

To extract the variants data for the other two individuals in
a file named ``HG00731_HG00732.vcf``, run::

    bcftools view \
    --samples HG00731,HG00732 \
    ALL.chr1.phase3_shapeit2_mvncall_integrated_v5a.20130502.genotypes.vcf.gz \
    > HG00731_HG00732.vcf


Importing the data into GPF
###########################

To import the collected data into the GPF system, it's recommended to use the
``impala_batch_import.py`` tool. To do so, run::

    impala_batch_import.py PR05.ped \
    --vcf-files HG00731_HG00732.vcf HG00733.vcf \
    --gs genotype_impala \
    --id 1KGP \
    -o parquet

.. note::

    To see a list of it's commands, use::

        impala_batch_import.py --help


Navigate to the newly created `parquet` directory::

    cd parquet

and run this command to initiate the importing::

    make -j 10

This command will take some time to complete.

Afer it's done, run the GPF web server::

    wdaemanage.py runserver 0.0.0.0:8000


Now you should be able to see the "1KGP" dataset. To view
the imported variants, navigate to the :ref:`genotype_browser_ui`
tab and click on the `Table Preview` button.
