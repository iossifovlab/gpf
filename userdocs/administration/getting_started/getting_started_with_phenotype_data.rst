Getting Started with Phenotype Data
###################################

Importing phenotype data
++++++++++++++++++++++++

To import phenotype data, the ``import_phenotypes`` tool is used.

The tool requires an **import project**, a YAML file describing the
contents of the phenotype data to be imported, along with configuration options
on how to import them.

As an example, we are going to show how to import simulated phenotype
data into our GPF instance.

Inside the ``input_phenotype_data`` directory, the following data is provided:

* ``instruments`` contains the phenotype instruments and measures to be imported.
* ``pedigree.ped`` is the corresponding pedigree file.
* ``measure_descriptions.tsv`` contains descriptions for the provided measures.
* ``import_project.yaml`` is the import project configuration that we will use 
  to import this data.

``input_phenotype_data/instruments/basic_medical.csv``:

.. literalinclude:: gpf-getting-started/input_phenotype_data/instruments/basic_medical.csv

``input_phenotype_data/instruments/iq.csv``:

.. literalinclude:: gpf-getting-started/input_phenotype_data/instruments/iq.csv

``input_phenotype_data/pedigree.ped``:

.. literalinclude:: gpf-getting-started/input_phenotype_data/pedigree.ped
    :tab-width: 10

``input_phenotype_data/measure_descriptions.tsv``:

.. literalinclude:: gpf-getting-started/input_phenotype_data/measure_descriptions.tsv
    :tab-width: 20

``input_phenotype_data/import_project.yaml``:

.. literalinclude:: gpf-getting-started/input_phenotype_data/import_project.yaml

.. note::

    For more information on how to import phenotype data see 
    :doc:`pheno`

To import the phenotype data, we will use the ``import_phenotypes`` tool. 
It will import the phenotype database directly to our GPF instance's phenotype 
storage:

.. code:: bash

    import_phenotypes input_phenotype_data/import_project.yaml

When the import finishes you can run the GPF development server using:

.. code-block:: bash

    wgpf run

Now on the GPF instance `Home Page` you should see the ``mini_pheno`` phenotype
study. 

.. figure:: getting_started_files/mini-pheno-home-page.png

    Home page with imported phenotype study


If you follow the link, you will see the `Phenotype Browser` tab with the
imported data.

.. figure:: getting_started_files/mini-pheno-phenotype-browser.png

    Phenotype Browser tab with imported data

In the `Phenotype Browser` tab you can search for phenotype instruments and
measures, see the aggregated figures for the measures, and download selected
instruments and measures.


Configure a genotype study to use phenotype data
++++++++++++++++++++++++++++++++++++++++++++++++

To demonstrate how a study is configured with a phenotype database, we will
be working with the already imported ``example_dataset`` dataset.

The phenotype databases can be attached to one or more studies and/or datasets.
If you want to attach the ``mini_pheno`` phenotype study to the 
``example_dataset`` dataset,
you need to specify it in the dataset's configuration file, which can be found at
``minimal_instance/datasets/example_dataset/example_dataset.yaml``.

Add the following line to the configuration file:

.. code:: yaml

    phenotype_data: mini_pheno

When you restart the server, you should be able to see `Phenotype Browser` 
and `Phenotype Tool` tabs enabled for the `Example Dataset` dataset.

Additionally, the `Family Filters` and `Person Filters` sections will have
the `Pheno Measures` filters enabled.

.. figure:: getting_started_files/example-dataset-genotype-browser-pheno-filters.png

    Example Dataset genotype browser using Pheno Measures family filters


Configure phenotype columns in Genotype Browser
+++++++++++++++++++++++++++++++++++++++++++++++

The Genotype Browser allows you to add phenotype columns to the table preview
and download file.

Phenotype columns show values from a phenotype database.
To configure such a column you need to specify following attributes:

* ``source`` - the measure ID which values we are going to show in the column;

* ``role`` - the role of the person in the family for which we are going to show
  the measure value;

* ``name`` - the display name of the column in the table.

Let's add a phenotype columns to the `Genotype Browser` preview table. 
To do this, you need to define it in the study's config, in the genotype 
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

* ``prb_verbal_iq`` - is a column that uses the value of the attribute
  ``iq.verbal_iq`` and formats it as a float with 5 decimal places. 
  The columns will be named `Verbal IQ` where it is used;

* ``prb_non_verbal_iq`` - is a column that uses the value of the attribute
  ``iq.non_verbal_iq``. The columns will be named `Non-Verbal IQ` where it is used.

In the preview table each column could show multiple values. In GPF when you
want to show multiple values in single column, you need to define a column group.

The column group is a collection of columns that are
shown together in the preview table. The values in a column group are shown
in a single cell. The column group is defined in the
``column_groups`` section of the configuration file.

In lines 38-42 we define a column group called `proband_iq` that contains the
columns ``prb_verbal_iq`` and ``prb_non_verbal_iq``.

To add the new column group ``proband_iq`` to the preview table, we need to add it to the
``preview_columns_ext`` section of the configuration file. In line 47 we
add the new column group ``proband_iq`` at the end of the preview table.

.. figure:: getting_started_files/example-dataset-proband-iq-column-group.png

    Example Dataset genotype browser using pheno measures columns
