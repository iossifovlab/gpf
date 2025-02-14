Getting Started with Phenotype Data
###################################

Setting up the GPF instance phenotype database
++++++++++++++++++++++++++++++++++++++++++++++

The GPF instance has four configuration settings that determine how phenotype data is read
and stored:

* The most important is the **phenotype data directory**, which is where the phenotype data
  configurations are. If not specified, will attempt to look for the environment variable ``DAE_PHENODB_DIR``,
  and if not found will default to the directory ``pheno`` inside the GPF instance directory.
* **Phenotype storages** can be configured to tell the GPF instance where to look for phenotype
  data DB files. If no phenotype storages are defined, a default phenotype storage is used,
  which uses the **phenotype data directory**
* The **cache** option can be configured to tell the GPF instance and GPF tools where to
  store generated phenotype browser data. Data will be stored inside the ``<cache_dir>/pheno`` directory.
* The **phenotype images** option can be configured to tell the GPF instance and GPF tools
  where to store generated phenotype browser images.

You can examine the provided ``gpf_instance.yaml`` to see how these settings are configured in it.

Importing phenotype data
++++++++++++++++++++++++

To import phenotype data, the ``import_phenotypes`` tool is used.

The tool requires an **import project**, a YAML file describing the
contents of the phenotype data to be imported, along with configuration options
on how to import them.

As an example, we are going to show how to import simulated phenotype
data into our GPF instance.

Inside the ``raw_phenotype_data`` directory, the following data is provided:

* ``instruments`` contains the phenotype instruments and measures to be imported.
* ``pedigree.ped`` is the corresponding pedigree file.
* ``measure_descriptions.tsv`` contains descriptions for the provided measures.
* ``import_project.yaml`` is the import project configuration that we will use to import this data.

To import the phenotype data, we will use the ``import_phenotypes.py`` tool. It will import
the phenotype database directly to our GPF instance's phenotype storage:

.. code:: bash

    import_phenotypes raw_phenotype_data/import_project.yaml

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
generated. You may inspect the ``minimal_instance/pheno/mini_pheno/mini_pheno.yaml``
configuration file generated from the import tool:

.. code:: yaml

    browser_images_url: static/images/
    id: mini_pheno
    name: mini_pheno
    phenotype_storage:
    db: mini_pheno/mini_pheno.db
    id: storage1
    regressions:
    reg_1:
        display_name: Regression one
        instrument_name: instrument_1
        jitter: 0.1
        measure_names:
        - measure_1
    type: study

Configure Genotype Study With Phenotype Data
++++++++++++++++++++++++++++++++++++++++++++

To demonstrate how a study is configured with a phenotype database, we will
be working with the already imported ``helloworld`` dataset.

The phenotype databases can be attached to one or more studies and/or datasets.
If you want to attach the ``mini_pheno`` phenotype study to the ``helloworld`` dataset,
you need to specify it in the dataset's configuration file, which can be found at
``minimal_instance/datasets/helloworld/helloworld.yaml``.

Add the following line at the beginning of the file, outside of any section:

.. code:: yaml

    phenotype_data: mini_pheno

To enable the :ref:`phenotype_browser_ui`, add this line:

.. code:: yaml

    phenotype_browser: true

After this, the beginning of the configuration file should look like this:

.. code:: yaml

    id: helloworld
    name: Hello World Dataset

    phenotype_data: mini_pheno
    phenotype_browser: true

    studies:
    - denovo_helloworld
    - vcf_helloworld

When you restart the server, you should be able to see the 'Phenotype Browser' tab in the `helloworld` dataset.

Configure Family Filters in Genotype Browser
+++++++++++++++++++++++++++++++++++++++++++++++

A study or a dataset can have phenotype filters configured for its :ref:`genotype_browser_ui`
when it has a phenotype database attached to it. The configuration looks like this:

.. code:: yaml

    genotype_browser:
      enabled: true
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

Configure Phenotype Columns in Genotype Browser
+++++++++++++++++++++++++++++++++++++++++++++++

Phenotype columns contain values from a phenotype database.
These values are selected from the individual who has the variant displayed in the :ref:`genotype_browser_ui`'s table preview.
They can be added when a phenotype database is attached to a study.

Let's add a phenotype column. To do this, you need to define it in the study's config,
in the genotype browser section:

.. code:: yaml

    genotype_browser:
      # ...
      columns:
        phenotype:
          sample_pheno_measure:
            role: prb
            source: instrument_1.measure_1
            name: Sample Pheno Measure Column

For the phenotype columns to be in the Genotype Browser table preview or download file, 
they have to be present in the ``preview_columns`` or the ``download_columns`` in the Genotype Browser
configuration. Add this in the genotype_browser section:

.. code:: yaml

    preview_columns:
    - family
    - variant
    - genotype
    - effect
    - gene_scores
    - sample_pheno_measure

Enabling the Phenotype Tool
+++++++++++++++++++++++++++

To enable the :ref:`phenotype_tool_ui` for a study, you must edit
the study's configuration file and set the appropriate property, as with
the :ref:`phenotype_browser_ui`. Open the helloworld dataset conifguration file
and add the following line:

.. code:: yaml

    phenotype_tool: true

After editing, it should look like this:

.. code:: yaml

    id: helloworld
    name: Hello World Dataset

    phenotype_data: mini_pheno
    phenotype_browser: true
    phenotype_tool: true

    studies:
    - denovo_helloworld
    - vcf_helloworld


Restart the GPF web server and select the ``helloworld`` dataset.
You should see the :ref:`phenotype_tool_ui` tab. Once you have selected it, you
can select a phenotype measure of your choice. To get the tool to acknowledge
the variants in the ``helloworld`` dataset, select the "All" option of the
"Present in Parent" field.

Click on the "Report" button to produce the results.
