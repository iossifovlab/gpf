Getting Started with Phenotype Data
###################################

Importing phenotype data
++++++++++++++++++++++++

The ``import_phenotypes`` tool is used to import phenotype data.

.. note::

    All the data files needed for this example are available in the
    `gpf-getting-started <https://github.com/iossifovlab/gpf-getting-started.git>`_
    repository under the subdirectory ``input_phenotype_data``.


The tool requires an **import project**, a YAML file describing the
contents of the phenotype data to be imported, along with configuration options
on how to import them.

As an example, we are going to show how to import a simulated phenotype
data into our GPF instance.

Inside the ``input_phenotype_data`` directory, the following data is provided:

* ``pedigree.ped`` is the phenotype data pedigree file.
  ``input_phenotype_data/pedigree.ped``:

  .. literalinclude:: gpf-getting-started/input_phenotype_data/pedigree.ped
      :tab-width: 12

* ``instruments`` contains the phenotype instruments and measures to be
  imported. There are two instruments in the example:

  .. csv-table:: ``input_phenotype_data/instruments/basic_medical.csv``
      :file: ../gpf-getting-started/input_phenotype_data/instruments/basic_medical.csv
      :header-rows: 1

  .. csv-table:: ``input_phenotype_data/instruments/iq.csv``
      :file: ../gpf-getting-started/input_phenotype_data/instruments/iq.csv
      :header-rows: 1

* ``measure_descriptions.tsv`` contains descriptions of the provided measures.

  ``input_phenotype_data/measure_descriptions.tsv``:

  .. literalinclude:: gpf-getting-started/input_phenotype_data/measure_descriptions.tsv
      :tab-width: 20

* ``import_project.yaml`` is the import project configuration that we will use
  to import this data.

  ``input_phenotype_data/import_project.yaml``:

  .. literalinclude:: gpf-getting-started/input_phenotype_data/import_project.yaml
       :lines: 1-25

.. note::

    For more information on how to import phenotype data, see
    :doc:`pheno`

We will use the ``import_phenotypes`` tool to import the phenotype data.
It will import the phenotype database directly to our GPF instance's phenotype
storage:

.. code:: bash

    import_phenotypes input_phenotype_data/import_project.yaml

When the import finishes, you can run the GPF development server using:

.. code-block:: bash

    wgpf run

Now, on the GPF instance `Home Page`, you should see the ``mini_pheno``
phenotype study.

.. figure:: getting_started_files/mini-pheno-home-page.png

    Home page with imported phenotype study


If you follow the link, you will see the `Phenotype Browser` tab with the
imported data.

.. figure:: getting_started_files/mini-pheno-phenotype-browser.png

    Phenotype Browser tab with imported data

In the `Phenotype Browser` tab, you can search for phenotype instruments and
measures, see the aggregated figures for the measures, and download selected
instruments and measures.


Configure a genotype study to use phenotype data
++++++++++++++++++++++++++++++++++++++++++++++++

To demonstrate how a study is configured with a phenotype database, we will
be working with the already configured ``example_dataset`` dataset.

The phenotype databases can be attached to one or more studies and/or datasets.
If you want to attach the ``mini_pheno`` phenotype study to the
``example_dataset`` dataset,
you need to specify it in the dataset's configuration file, which can be found
at ``minimal_instance/datasets/example_dataset/example_dataset.yaml``.

Add the following line to the configuration file:

.. code:: yaml

    phenotype_data: mini_pheno

When you restart the server, you should be able to see `Phenotype Browser`
and `Phenotype Tool` tabs enabled for the `Example Dataset` dataset.

Additionally, in the `Genotype Browser`, the `Family Filters` and
`Person Filters` sections will have the `Pheno Measures` filters enabled.

.. figure:: getting_started_files/example-dataset-genotype-browser-pheno-filters.png

    Example Dataset genotype browser using Pheno Measures family filters
