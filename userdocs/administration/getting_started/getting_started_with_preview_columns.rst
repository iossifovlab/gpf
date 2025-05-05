.. _getting_started_with_preview_columns:

Getting Started with Preview Columns
####################################

Configure genotype columns in Genotype Browser
+++++++++++++++++++++++++++++++++++++++++++++++

Once you have annotated your variants, the additional attributes 
produced by the annotation can be displayed in the variants preview table.

In our example, the annotation produces three additional attributes:

* ``gnomad_v4_genome_ALL_af``;
* ``CLNSIG``;
* ``CLNDN``.


Let us add these attributes to the
variants preview table and the variants download file for the
``example_dataset`` dataset.

In the preview table, each column could show multiple values.
In GPF, when you want to show multiple values in a single column,
you need to define a **column group**.

The column group is a collection of attributes that are
shown together in the preview table. The values in a column group are shown
in a single cell. 

By default, the study configuration includes several predefined columns groups:
``family``, ``variant``, ``genotype``, ``effect`` and ``frequency``. 

.. figure:: getting_started_files/example-dataset-default-column-groups.png

    Default column groups in the `Preview Table`

In the
study configuration you can define your own column groups or redefine already
existing ones. Let us redefine the existing column group
``frequency`` to include the gnomAD frequency and define a new column group 
``clinvar`` to include the ClinVar attributes.

The column group is defined in the
``column_groups`` section of the configuration file.

Edit the ``example_dataset.yaml`` dataset configuration in
``minimal_instance/datasets/example_dataset`` and add the following section
at the end of the configuration file:

.. code-block:: yaml
    :linenos:
    :emphasize-lines: 3-7,9-13,15-16

    genotype_browser:
      column_groups:
        frequency:
          name: frequency
          columns:
          - allele_freq
          - gnomad_v4_genome_ALL_af

        clinvar:
          name: ClinVar
          columns:
          - CLNSIG
          - CLNDN

      preview_columns_ext:
        - clinvar

In lines 3-7, we re-define the existing column group
``frequency`` to include the study frequency ``allele_freq`` and gnomAD
frequency ``gnomad_v4_genome_ALL_af``.

In lines 9-13, we define a new column group
``clinvar`` that contains the values of the annotation attributes
``CLNSIG`` and ``CLNDN``.

In lines 15-16, we extend the preview table columns. The new column groups
``clinvar`` will be added to the preview table.

If we now stop the ``wgpf`` tool and run it again, we will be able to see
the new columns in the preview table and in the download file.

From the GPF instance `Home Page`, follow the link to the `Example Dataset` page
and choose the `Genotype Browser`. Select all checkboxes in `Present in Child`,
`Present in Parent` and `Effect Types` sections.

.. image:: getting_started_files/example-dataset-genotype-browser-extended-columns-filters.png

Then click the `Preview` button and will be able to see all the imported
variants with their additional attributes coming from the annotation.

.. figure:: getting_started_files/example-dataset-genotype-browser-extended-columns-variants.png

    Example Dataset genotype browser displaying variants with additional
    columns `gnomAD v4` and `ClinVar`.


Configure phenotype columns in Genotype Browser
+++++++++++++++++++++++++++++++++++++++++++++++

The Genotype Browser allows you to add phenotype attributes to the table preview
and the download file.

Phenotype attributes show values from a phenotype database that are associated
with the displayed family variant.
To configure such a column, you need to specify the following properties:

* ``source`` - the measure ID whose values will be shown in the column;

* ``role`` - the role of the person in the family for which we are going to
  show the phenotype measure value;

* ``name`` - the display name of the column in the table.

Let's add some phenotype columns to the `Genotype Browser` preview table
in `Example Dataset`.
To do this, you need to define them in the study's config, in the genotype
browser section of the configuration file. 
We are going to modify the
``example_dataset.yaml`` dataset configuration in
``minimal_instance/datasets/example_dataset/example_data.yaml``:

.. code-block:: yaml
    :linenos:
    :emphasize-lines: 2-12,27-31,35

    genotype_browser:
      columns:
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
        frequency:
          name: frequency
          columns:
          - allele_freq
          - gnomad_v4_genome_ALL_af

        clinvar:
          name: ClinVar
          columns:
          - CLNSIG
          - CLNDN

        proband_iq:
          name: Proband IQ
          columns:
          - prb_verbal_iq
          - prb_non_verbal_iq

      preview_columns_ext:
        - clinvar
        - proband_iq


Lines 2-12 define the two new columns with values coming from the phenotype data
attributes:

* ``prb_verbal_iq`` - is a column that uses the value of the phenotype measure
  ``iq.verbal_iq`` for the family proband.
  The display name of the column will be `Verbal IQ`;

* ``prb_non_verbal_iq`` - is a column that uses the value of the phenotype
  measure ``iq.non_verbal_iq`` for the family proband.
  The display name of the column will be `Non-Verbal IQ`.

We want these two columns to be shown together in the preview table. To do this,
we need to define a new **column group**.
In lines 27-31, we define a column group called ``proband_iq`` that contains the
columns ``prb_verbal_iq`` and ``prb_non_verbal_iq``.

To add the new column group ``proband_iq`` to the preview table, we need to
add it to the ``preview_columns_ext`` section of the configuration file.
In line 35, we add the new column group ``proband_iq`` at the end of the
preview table.


When you restart the server, go to the `Genotype Browser` tab of the
``Example Dataset`` dataset and select all checkboxes in `Present in Child`,
`Present in Parent` and `Effect Types` sections:

.. image:: getting_started_files/example-dataset-proband-iq-column-group-filters.png

When you click on the `Table Preview` button, you will be able to see the new
column group ``proband_iq`` in the preview table.

.. figure:: getting_started_files/example-dataset-proband-iq-column-group-variants.png

    Example Dataset genotype browser using pheno measures columns
