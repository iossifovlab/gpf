Getting Started with Preview and Download Columns
#################################################

When importing data into a GPF instance we can run an annotation pipeline that
adds additional attributes to each variant. To make these attributes available in
the variants preview table and in the variants download file we need to change
the configuration of the corresponding study or dataset.

For each study dataset, you can specify which columns are shown in the variants' 
table preview, as well as those which will be downloaded.

Example: Redefine the `Frequency` column in the preview table of `Example Dataset`
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

As an example, we are going to redefine the `Frequency` column for ``example_dataset``
dataset to include attributes from annotation with GnomAD v4 genomic score.

Edit the ``example_dataset.yaml`` dataset configuration in ``minimal_instance/datasets/example_dataset``:

Add the following section to the end:

.. code-block:: yaml

    genotype_browser:
      columns:
        genotype:
          gnomad_v4_genome_ALL_af:
            name: gnomAD v4 AF
            source: gnomad_v4_genome_ALL_af
            format: "%%.3f"
      column_groups:
        freq:
          name: "Frequency"
          columns: 
            - gnomad_v4_genome_ALL_af

This overwrites the definition of the default preview column `Frequency` to
include the gnomAD v4 frequencies. If we now browse the `Example Dataset`
and run variants preview in the genotype browser we will start seeing the 
GnomAD attributes:

.. image:: getting_started_files/helloworld-gnomad-frequency-preview-columns.png


Example: Add GnomAD v4 column to the variants download
++++++++++++++++++++++++++++++++++++++++++++++++++++++

As an example let us add the GnomAD v4 column to the variants downloads.

By default, each genotype study or dataset has a list of predefined columns used
when downloading variants. The users can replace the default list of download
columns by defining the ``download_columns`` list or they can extend the predefined
list of download columns by defining the ``download_columns_ext`` list of columns.

In the example below we are going to use ``download_columns_ext`` to add
the GnomAD v4 column to the properties of downloaded variants:

.. code-block:: yaml

    genotype_browser:
      columns:
        genotype:
          gnomad_v4_genome_ALL_af:
            name: gnomAD v4 AF
            source: gnomad_v4_genome_ALL_af
            format: "%%.3f"
      column_groups:
        freq:
          name: "Frequency"
          columns: 
            - gnomad_v4_genome_ALL_af

      download_columns_ext:
        - gnomad_v4_genome_ALL_af

