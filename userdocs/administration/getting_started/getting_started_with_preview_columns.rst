Getting Started with Preview and Download Columns
#################################################

Once you have annotated your variants the additional attributes produced by the
annotation can be used in the variants preview table and in the variants download
file. For each study dataset, you can specify which columns are shown in the 
variants' table preview, as well as those which will be downloaded.

In our example the annotation produces two additional attributes:
``gnomad_v4_genome_ALL_af`` and ``CLNSIG``. Let us add these attributes to the
variants preview table and the variants download file for the ``example_dataset``
dataset.

Edit the ``example_dataset.yaml`` dataset configuration in 
``minimal_instance/datasets/example_dataset`` and add the following section
at the end of the configuration file:

.. code-block:: yaml
    :linenos:

    genotype_browser:
      columns:
        genotype:
          gnomad_v4_genome_af:
            name: gnomAD v4 AF
            source: gnomad_v4_genome_ALL_af
            format: "%%.5f"
          clinvar_clinsig:
            name: ClinVar CLINSIG
            source: CLNSIG

      preview_columns_ext:
        - gnomad_v4_genome_af
        - clinvar_clinsig

      download_columns_ext:
        - gnomad_v4_genome_af
        - clinvar_clinsig


Lines 3-10 define two new columns with values comming from the genotype data
attributes:

* ``gnomad_v4_genome_af`` - is a column that uses the value of the attribute
  ``gnomad_v4_genome_ALL_af`` and formats it as a float with 5 decimal places. 
  The columns will be named `gnomAD v4 AF` where it is used;

* ``clinvar_clinsig`` - is a column that uses the value of the attribute
  ``CLNSIG``. The columns will be named `ClinVar CLINSIG` where it is used.

In line 12-14 we extend the preview table columns. The new columns 
``gnomad_v4_genome_af`` and ``clinvar_clinsig`` will be added to the preview table.

In lines 16-18 we extend the download file columns. The new columns 
``gnomad_v4_genome_af`` and ``clinvar_clinsig`` will be added to the download file.

If we now stop the ``wgpf`` tool and run it again, we will be able to see the new
columns in the preview table and in the download file.

From the GPF instance `Home Page` follow the link to the `Example Dataset` page
and choose the genotype browser. Select all checkboxes in `Present in Child`, 
`Present in Parent` and `Effect Types` sections and click the `Preview` button.


.. figure:: getting_started_files/example-dataset-genotype-brower-extended-columns-2.png

    Example Dataset genotype browser with additional columns `gnomAD v4 AF` 
    and `ClinVar CLINSIG`.
