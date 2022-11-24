Getting Started with Gene Browser
#################################

The Gene Browser in the GPF system uses the allele frequency as a Y-coordinate
when displaying the allele. By default, the allele frequency used is the frequency
of the alleles in the imported data.

.. image:: getting_started_files/helloworld-gene-browser-study-frequency.png

After annotation of the ``helloworld`` data with GnomAD v3 we can use the GnomAD
allele frequency in the Gene Browser.

Example: configure the gene browser to use gnomAD frequency as the variant frequency
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

To configure the `Hello World Dataset` to use GnomAD v3 allele frequency 
we need to add a new section
``gene_browser`` in the configuration file of the datasets 
``datasets/helloworld/helloworld.yaml`` as follows:

.. code-block:: yaml

    id: helloworld
    name: Hello World Dataset

    ...

    gene_browser:
      frequency_column: genome_gnomad_v3_af_percent


If we restart the GPF development server and navigate to ``Hello World Dataset``
Gene Browser, the Y-axes will use the GnomAD allele frequency instead of the
study allele frequency.

.. image:: getting_started_files/helloworld-gene-browser-gnomad-frequency.png

