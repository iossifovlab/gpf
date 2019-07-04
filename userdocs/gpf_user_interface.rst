GPF User Interface
==================

The data are organized by datasets. Each dataset represents a set of families and the available phenotypic and genotypic data for the members of these families. Typically, a user selects a dataset to operate on first and then uses the applicable view or tool over the selected data set organized as tabs (See Figure 1). Alternatively, a user can use of the meta-analysis tools that allow simultaneous queries over all datasets he has access to. Finally, the system provides a management interface allowing the system administrator to control the registered users and the datasets they are authorized to access. We provide a brief description of the available tools below.


Dataset Tools
*************

Dataset Description
-------------------

The “Dataset Description” provides a high level description of the dataset. The description can contain the reason for building the dataset, its size and scope, its rules for access and usage, details of the technology used to generate the phenotypic and genotypic data, and relevant references

Dataset Statistics
------------------

The “Dataset Statistics” (Common Reports) shows the number of people by role (proband, mother, grandfather, etc), by primary diagnosis, or other relevant phenotypic parameters. Additionally, the “Dataset Statistics” tab shows the number of families by pedigree structure and, if applicable, the rates of de novo variants by variant type and effect and by person’s role and diagnosis (see Figure 2).


Genotype Browser
----------------

The “Genotype Browser” provides a powerful query interface to the dataset’s genetic variants. User can filter variants based properties of the variants like: their type (SNP, short indel, CNV); their effect on proteins (i.e. missense, synonymous, LGD, etc.); whether they are  de novo or transmitted and their frequency; genomic scores assigned to variants (i.e. phyloP, CADD, MPC, etc.); the genes targeted by the variant; and the family the variant occurs in.  Also, the user can filter by properties of the target genes, like protection scores (pLI, RVIS, etc.), pathway membership and SFARI Gene score and phenotypic properties associated with individuals in the ataset families. After the query is set up the user can preview the variants of interest within the website of download them as an Excel file for further analysis. Figure 3 shows two example queries and the GPFs user documentation (???)  provides a more detailed description “Genotype Browsers”’s functionality.

Phenotype Browser
-----------------

The “Phenotype Browser” shows the phenotypic data associated with a data set. The Phenotypic data is organized by ‘Instruments’ applied to individuals and each instrument has a set of measures. The user can easily see all the instruments and all the measures within each instrument represented by the histograms of the measures across the individuals in the datasets split by role and diagnosis. In addition, the “Phenotype Browser” provides a simple keyword search for measures of interest. (See Figure 4) and allows the user to download the data in Excell form for further analysis. 

Enrichment Tool
---------------

The “Enrichment Tool” allows the user to test if a given set of genes is affected by more or less by de novo mutations than expected in the children in the dataset. We and other have used such a simple approach to demonstrate that there is functional convergence of de novo mutations in autism (i.e., damaging de novo mutations in children with autism target synaptic genes and genes encoding chromatin modifiers) and that the de novo mutation in autism target similar genes as the de novo mutation in intellectual disability and epilepsy but same technique was applied in studies of various other disorder. Moreover, users can use the “Enrichment tool” over existing datasets to tests hypothesis driven by their own research against the large genetic data managed by GPF. (See Figure 5)

Pheno Tool
----------

The “Pheno Tool” (Figure 6)

metaTools
*********

MetaQuery
---------

The “metaQuery” (“All data sets”)

Management Tools
****************

.. toctree::
   :maxdepth: 3

   user_management
   users
   groups
   datasets
