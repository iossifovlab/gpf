Getting Started with Preview and Download Columns
#################################################

When importing data into a GPF instance we can run an annotation pipeline that
adds additional attributes to each variant. To make these attributes available in
the variants preview table and in the variants download file we need to change
the configuration of the corresponding study or dataset.

For each study dataset, you can specify which columns are shown in the variants' 
table preview, as well as those which will be downloaded.

Example: Redefine the `Frequency` column in the preview table of `Hello World Dataset`
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

As an example, we are going to redefine the `Frequency` column for ``helloworld``
dataset to include attributes from annotation with GnomAD v3 genomic score.

Navigate to the ``helloworld`` dataset folder:

.. code-block:: bash

    cd minimal_instance/datasets/helloworld

and edit the ``helloworld.yaml`` file. Add the following section to the end:

.. code-block:: yaml

    genotype_browser:
      columns:
        genotype:
          genome_gnomad_v3_af_percent:
            name: gnomAD v3 AF
            source: genome_gnomad_v3_af_percent
            format: "%%.3f"
          genome_gnomad_v3_ac:
            name: gnomAD v3 AC
            source: genome_gnomad_v3_ac
            format: "%%d"
          genome_gnomad_v3_an:
            name: gnomAD v3 AN
            source: genome_gnomad_v3_an
            format: "%%d"
      column_groups:
        freq:
          name: "Frequency"
          columns: 
            - genome_gnomad_v3_af_percent
            - genome_gnomad_v3_ac
            - genome_gnomad_v3_an    

This overwrites the definition of the default preview column `Frequency` to
include the gnomAD v3 frequencies. If we now browse the `Hello World Dataset`
and run variants preview in the genotype browser we will start seeing the 
GnomAD attributes:

.. image:: getting_started_files/helloworld-gnomad-frequency-preview-columns.png


Example: Add GnomAD v3 columns to the variants download
+++++++++++++++++++++++++++++++++++++++++++++++++++++++

As an example let us add GnomAD v3 columns to the variants downloads.

By default, each genotype study or dataset has a list of predefined columns used
when downloading variants. The users can replace the default list of download
columns by defining the ``download_columns`` list or they can extend the predefined
list of download columns by defining the ``download_columns_ext`` list of columns.

In the example below we are going to use ``download_columns_ext`` to add
GnomAD v3 columns to the properties of downloaded variants:

.. code-block:: yaml

    genotype_browser:
      columns:
        genotype:
          genome_gnomad_v3_af_percent:
            name: gnomAD v3 AF
            source: genome_gnomad_v3_af_percent
            format: "%%.3f"
          genome_gnomad_v3_ac:
            name: gnomAD v3 AC
            source: genome_gnomad_v3_ac
            format: "%%d"
          genome_gnomad_v3_an:
            name: gnomAD v3 AN
            source: genome_gnomad_v3_an
            format: "%%d"
      column_groups:
        freq:
          name: "Frequency"
          columns: 
            - genome_gnomad_v3_af_percent
            - genome_gnomad_v3_ac
            - genome_gnomad_v3_an    

      download_columns_ext:
        - genome_gnomad_v3_af_percent
        - genome_gnomad_v3_ac
        - genome_gnomad_v3_an    

