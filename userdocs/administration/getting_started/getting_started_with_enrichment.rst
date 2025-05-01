Getting Started with Enrichment Tool
####################################

By default, for each genotype study with de Novo variants, the GPF system
enables the Enrichment tool.

The Enrichment Tool allows the user to test if a given set of genes is affected
by more or fewer de novo mutations in the children in the dataset than expected.

To use the Enrichment Tool, a user must choose a set of genes either by 
selecting one of the gene sets that have already been loaded in GPF or by 
providing their own gene set.

The user also must select among the background models that GPF uses to 
compute the expected number of de novo mutations within the given dataset. 

.. note::

    By default, for studies with de Novo variants, only one background model 
    is configured: `enrichment/samocha_background
    <https://grr.iossifovlab.com/enrichment/samocha_background/index.html>`_

    The use other background models the user must edit the study configuration
    file.

If you navigate to the `Enrichment Tool` page for the ``ssc_denovo`` study,
you will be able to use the tool with run different tests.

.. figure:: getting_started_files/ssc_denovo_enrichment_tool.png

   Enrichment Tool for ``ssc_denovo`` study.
