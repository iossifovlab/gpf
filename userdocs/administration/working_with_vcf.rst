Working With VCF Files Guide
============================


How to import data from the '1000 Genome Project'
#################################################

The data used in this guide is from the '1000 Genome Project'.
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

.. note::
    The variants files are in `Variant Call Format` (.vcf) format


Creating the pedigree file
##########################

Information about the individual's relationships within their family can be found
in the spreadsheet file ``20130606_sample_info.xlsx``, in the 'Sample Info' tab.
Let's create a pedigree file for the family with id "PR05". For more information on working with pedigree files,
refer to the :ref:`Working With Pedigrees Guide <working_with_pedigrees>`.

First, create the pedigree file:

.. code-block:: bash

    touch PR05.ped

Then open it in a text editor and add the necessary columns - familyId, personId, momId, dadId, sex, status and role.
Fill in the individuals and the values in each column, by refering to the spreadsheet for information.
After the editing, the pedigree file should look like this:

.. code-block::

    familyId	personId	momId	dadId	sex	status	role
    PR05	HG00731	0	0	M	unaffected	dad
    PR05	HG00732	0	0	F	unaffected	mom
    PR05	HG00733	HG00732	HG00731	M	affected	prb

Next, you have to standardize the pedigree file, using the ``ped2ped.py`` tool::

    ped2ped.py PR05.ped -o PR05_standardized.ped --ped-layout-mode generate

This command will generate a new pedigree file - ``PR05_standardized.ped`` with
two newly added columns - sampleId and layout, which will be used
by the GPF system. Now the pedigree file is ready for importing.


Creating the VCF files
######################

Now with the pedigree file ready, you can create the files with the variants data.
To do so, you can use `Bcftools <https://samtools.github.io/bcftools/>`_.

To install bcftools into your anaconda environment, use::

    conda install -c bioconda bcftools

.. note::

    To see a list of bcftools' commands, use::

        bcftools --help


The two .vcf files you downloaded earlier contain a lot of inviduals. Let's start with the related samples first,
which are in the ``ALL.chr1.phase3_shapeit2_mvncall_integrated_v5_related_samples.20130502.genotypes.vcf.gz`` file.
Use bcftools' ``view`` command to inspect the files. 

This command will print the first 250 lines of the vcf (`head -n 250`) in the terminal::

    bcftools view ALL.chr1.phase3_shapeit2_mvncall_integrated_v5_related_samples.20130502.genotypes.vcf.gz \
    | head -n 250


You can also use this command to only print the 250th line::

    bcftools view ALL.chr1.phase3_shapeit2_mvncall_integrated_v5_related_samples.20130502.genotypes.vcf.gz \
    | sed -n '250p'


Keep in mind that vcf files are tab separated and have rows and columns. To extract individual `HG00733`'s data from the file,
firstly we need to know their column's index. If you run::

    bcftools view ALL.chr1.phase3_shapeit2_mvncall_integrated_v5_related_samples.20130502.genotypes.vcf.gz \
    | head -n 250 \
    | cut -f 1,2,3,4,5,6,7,8,9


You will see the first 250 rows of the first 9 columns (cut -f 1,2,3...9). The individual you are interested in
is in the 14th column. Remove the `head -n 250` to get all the data, add `14` to the `cut -f` list and
use `> HG00733.vcf` in the end, to save the result of this command into a file, named ``HG00733.vcf``::

    bcftools view ALL.chr1.phase3_shapeit2_mvncall_integrated_v5_related_samples.20130502.genotypes.vcf.gz \
    | cut -f 1,2,3,4,5,6,7,8,9,14 \
    > HG00733.vcf


The data for individuals HG00731 and HG00732 is in the second
vcf file - ``ALL.chr1.phase3_shapeit2_mvncall_integrated_v5a.20130502.genotypes.vcf.gz``.

To extract the variants data for the other two individuals, run::

    bcftools view ALL.chr1.phase3_shapeit2_mvncall_integrated_v5a.20130502.genotypes.vcf.gz \
    | cut -f 1,2,3,4,5,6,7,8,9,307,308 \
    > HG00731_HG00732.vcf

This command will save the variants data into a file named ``HG00731_HG00732.vcf``.
It will take more time than the previous command.


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

This command will take some time.
