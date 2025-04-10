Getting Started with Gene Browser
#################################

The Gene Browser in the GPF system uses the allele frequency as a Y-coordinate
when displaying the allele. By default, the allele frequency used is the frequency
of the alleles in the imported data.

.. image:: getting_started_files/helloworld-gene-browser-study-frequency.png

After annotation of the ``example_dataset`` data with GnomAD v4 we can use the GnomAD
allele frequency in the Gene Browser.

Example: configure the gene browser to use gnomAD frequency as the variant frequency
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

To configure the `Example Dataset` to use GnomAD v4 allele frequency 
we need to add a new section
``gene_browser`` in the configuration file of the datasets 
``datasets/example_dataset/example_dataset.yaml`` as follows:

.. code-block:: yaml

    id: example_dataset
    name: Example Dataset

    ...

    gene_browser:
      enabled: true
      frequency_column: gnomad_v4_genome_ALL_af


If we restart the GPF development server and navigate to ``Example Dataset``
Gene Browser, the Y-axes will use the GnomAD allele frequency instead of the
study allele frequency.

.. image:: getting_started_files/helloworld-gene-browser-gnomad-frequency.png

