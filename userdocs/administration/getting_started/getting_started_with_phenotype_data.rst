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
* ``import_project.yaml`` is the import project configuration that we will use to import this data.

To import the phenotype data, we will use the ``import_phenotypes.py`` tool. It will import
the phenotype database directly to our GPF instance's phenotype storage:

.. code:: bash

    import_phenotypes input_phenotype_data/import_project.yaml

When the import finishes you can run the GPF development server using:

.. code-block:: bash

    wgpf run

This will generate a phenotype browser database automatically, and the phenotype study should be directly accessible.

Phenotype browser databases are necessary to view the data through the web application. They are further described in the phenotype data documentation.

Configuring a phenotype database
++++++++++++++++++++++++++++++++

Phenotype databases have a short configuration file which points
the system to their files, as well as specifying additional properties.
When importing a phenotype database through the
``import_phenotypes`` tool, a configuration file is automatically
generated at ``minimal_instance/pheno/mini_pheno/mini_pheno.yaml``.

Configure a genotype study to use phenotype data
++++++++++++++++++++++++++++++++++++++++++++++++

To demonstrate how a study is configured with a phenotype database, we will
be working with the already imported ``example_dataset`` dataset.

The phenotype databases can be attached to one or more studies and/or datasets.
If you want to attach the ``mini_pheno`` phenotype study to the ``example_dataset`` dataset,
you need to specify it in the dataset's configuration file, which can be found at
``minimal_instance/datasets/example_dataset/example_dataset.yaml``.

Add the following line to the file:

.. code:: yaml

    phenotype_data: mini_pheno

To enable the :ref:`Phenotype Browser`, add this line:

.. code:: yaml

    phenotype_browser: true

When you restart the server, you should be able to see the 'Phenotype Browser' tab in the ``example_dataset`` dataset.

Configure family filters in Genotype Browser
++++++++++++++++++++++++++++++++++++++++++++

A study or a dataset can have phenotype filters configured for its :ref:`Genotype Browser`
when it has a phenotype database attached to it. The configuration looks like this:

.. code:: yaml

    genotype_browser:
      ...
      family_filters:
        sample_continuous_filter:
          name: Sample Filter Name
          source_type: continuous
          from: phenodb
          filter_type: multi
          role: prb

After adding the family filters configuration, restart the web server and
navigate to the Genotype Browser. You should be able to see the Advanced option
under the Family Filters - this is where the family filters can be applied.

Configure phenotype columns in Genotype Browser
+++++++++++++++++++++++++++++++++++++++++++++++

Phenotype columns contain values from a phenotype database.
These values are selected from the individual who has the variant displayed in the :ref:`Genotype Browser`'s table preview.
They can be added when a phenotype database is attached to a study.

Let's add a phenotype column. To do this, you need to define it in the study's config,
in the genotype browser section:

.. code:: yaml

    genotype_browser:
      columns:
        genotype:
          ...
        phenotype:
          sample_pheno_measure:
            role: prb
            source: instrument_1.measure_1
            name: Sample Pheno Measure Column

For the phenotype columns to be in the Genotype Browser table preview or download file, 
they have to be present in the ``preview_columns`` or the ``download_columns`` in the Genotype Browser
configuration. Add this to the genotype browser section:

.. code:: yaml

    genotype_browser:
      ...
      preview_columns:
        - family
        - variant
        - genotype
        - effect
        - gene_scores
        - sample_pheno_measure
