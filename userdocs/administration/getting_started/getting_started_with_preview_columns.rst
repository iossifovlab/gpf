.. _getting_started_with_preview_columns:

Getting Started with Preview and Download Columns
#################################################

Configure genotype columns in Genotype Browser
+++++++++++++++++++++++++++++++++++++++++++++++

Once you have annotated your variants the additional attributes produced by the
annotation can be used in the variants preview table and in the variants
download file. For each study and dataset you can specify which columns are
shown in the variants' table preview, as well as those which will
be downloaded.

In our example the annotation produces three additional attributes:
``gnomad_v4_genome_ALL_af``, ``CLNSIG``, and ``CLNDN``. Let us add these
attributes to the
variants preview table and the variants download file for the
``example_dataset`` dataset.

Edit the ``example_dataset.yaml`` dataset configuration in
``minimal_instance/datasets/example_dataset`` and add the following section
at the end of the configuration file:

.. code-block:: yaml
    :linenos:
    :emphasize-lines: 3-13, 16-19, 21-25, 27-29, 31-34

    genotype_browser:
      columns:
        genotype:
          gnomad_v4_genome_af:
            name: gnomAD v4 AF
            source: gnomad_v4_genome_ALL_af
            format: "%%.5f"
          clinvar_clnsig:
            name: CLNSIG
            source: CLNSIG
          clinvar_clndn:
            name: CLNDN
            source: CLNDN

      column_groups:
        gnomad_v4:
          name: gnomAD v4
          columns:
          - gnomad_v4_genome_af

        clinvar:
          name: ClinVar
          columns:
          - clinvar_clnsig
          - clinvar_clndn

      preview_columns_ext:
        - gnomad_v4
        - clinvar

      download_columns_ext:
        - gnomad_v4_genome_af
        - clinvar_clnsig
        - clinvar_clndn


Lines 3-13 define the three new columns with values comming from the
genotype data attributes:

* ``gnomad_v4_genome_af`` - is a column that uses the value of the attribute
  ``gnomad_v4_genome_ALL_af`` and formats it as a float with 5 decimal places.
  The display name of the column will be `gnomAD v4 AF`;

* ``clinvar_clnsig`` - is a column that uses the value of the attribute
  ``CLNSIG``. The display name of the column will be `CLNSIG`;

* ``clinvar_clndn`` - is a column that uses the value of the attribute
  ``CLNDN``. The display name of the column will be `CLNDN`.

In the preview table each column could show multiple values. In GPF when you
want to show multiple values in single column, you need to define a \
**column group**.

The column group is a collection of columns that are
shown together in the preview table. The values in a column group are shown
in a single cell. The column group is defined in the
``column_groups`` section of the configuration file.

In lines 16-19 we define a column group
``gnomad_v4`` that contains the column
``gnomad_v4_genome_af``.

In lines 21-25 we define a column group
``clinvar`` that contains the columns
``clinvar_clnsig`` and ``clinvar_clndn``.


In lines 27-29 we extend the preview table columns. The new column groups
``gnomad_v4`` and ``clinvar`` will be added to the preview table.

In lines 32-34 we extend the download file columns. The columns
``gnomad_v4_genome_af``, ``clinvar_clnsig``, ``clinvar_clndn`` will be added
to the download file.

If we now stop the ``wgpf`` tool and run it again, we will be able to see
the new columns in the preview table and in the download file.

From the GPF instance `Home Page` follow the link to the `Example Dataset` page
and choose the `Genotype Browser`. Select all checkboxes in `Present in Child`,
`Present in Parent` and `Effect Types` sections.

.. image:: getting_started_files/example-dataset-genotype-browser-extended-columns-filters.png

Then click the `Preview` button and will be able to see all the imported
variants with their additional attributes comming from the annotation.

.. figure:: getting_started_files/example-dataset-genotype-browser-extended-columns-variants.png

    Example Dataset genotype browser displaying variants with additional
    columns `gnomAD v4` and `ClinVar`.


Configure phenotype columns in Genotype Browser
+++++++++++++++++++++++++++++++++++++++++++++++

The Genotype Browser allows you to add phenotype columns to the table preview
and download file.

Phenotype columns show values from a phenotype database.
To configure such a column you need to specify following attributes:

* ``source`` - the measure ID which values we are going to show in the column;

* ``role`` - the role of the person in the family for which we are going to
   show the phenotype measure value;

* ``name`` - the display name of the column in the table.

Let's add a phenotype columns to the `Genotype Browser` preview table.
To do this, you need to define them in the study's config, in the genotype
browser section of the configuration file.

.. code-block:: yaml
    :linenos:
    :emphasize-lines: 15-24,38-42,47,53-54

    genotype_browser:
      columns:
        genotype:
          gnomad_v4_genome_af:
            name: gnomAD v4 AF
            source: gnomad_v4_genome_ALL_af
            format: "%%.5f"
          clinvar_clnsig:
            name: CLNSIG
            source: CLNSIG
          clinvar_clndn:
            name: CLNDN
            source: CLNDN

        phenotype:
          prb_verbal_iq:
            role: prb
            name: Verbal IQ
            source: iq.verbal_iq

          prb_non_verbal_iq:
            role: prb
            name: Non-Verbal IQ
            source: iq.non_verbal_iq

      column_groups:
        gnomad_v4:
          name: gnomAD v4
          columns:
          - gnomad_v4_genome_af

        clinvar:
          name: ClinVar
          columns:
          - clinvar_clnsig
          - clinvar_clndn

        proband_iq:
          name: Proband IQ
          columns:
          - prb_verbal_iq
          - prb_non_verbal_iq

      preview_columns_ext:
        - gnomad_v4
        - clinvar
        - proband_iq

      download_columns_ext:
        - gnomad_v4_genome_af
        - clinvar_clnsig
        - clinvar_clndn
        - prb_verbal_iq
        - prb_non_verbal_iq


Lines 15-24 define two new columns with values coming from the phenotype data
attributes:

* ``prb_verbal_iq`` - is a column that uses the value of the phenotype measure
  ``iq.verbal_iq`` for the family proband.
  The display name of the column will be `Verbal IQ`;

* ``prb_non_verbal_iq`` - is a column that uses the value of the phenotype
  measure ``iq.non_verbal_iq`` for the family proband.
  The display name of the column will be `Non-Verbal IQ`.

In the preview table each column could show multiple values. In GPF when you
want to show multiple values in single column, you need to define
a **column group**.

The column group is a collection of columns that are
shown together in the preview table. The values in a column group are shown
in a single cell. The column group is defined in the
``column_groups`` section of the configuration file.

In lines 38-42 we define a column group called `proband_iq` that contains the
columns ``prb_verbal_iq`` and ``prb_non_verbal_iq``.

To add the new column group ``proband_iq`` to the preview table, we need to
add it to the ``preview_columns_ext`` section of the configuration file.
In line 47 we add the new column group ``proband_iq`` at the end of the
preview table.


When you restart the server, go to the `Genotype Browser` tab of the
``Example Dataset`` dataset and select all checkboxes in `Present in Child`,
`Present in Parent` and `Effect Types` sections:

.. image:: getting_started_files/example-dataset-proband-iq-column-group-filters.png

When you click on the `Table Preview` button, you will be able to see the new
column group ``proband_iq`` in the preview table.

.. figure:: getting_started_files/example-dataset-proband-iq-column-group-variants.png

    Example Dataset genotype browser using pheno measures columns
