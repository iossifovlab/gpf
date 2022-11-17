Getting Started with Phenotype Data
###################################

Simple Pheno Import Tool
++++++++++++++++++++++++

The GPF simple pheno import tool prepares phenotype data to be used by the GPF
system.

As an example, we are going to show how to import simulated phenotype 
data into our GPF instance.

Download the archive and extract it outside of the GPF instance data directory:

.. code::

    wget -c https://iossifovlab.com/distribution/public/pheno/phenotype-comp-data-latest.tar.gz
    tar zxvf phenotype-comp-data-latest.tar.gz

Navigate to the newly created ``comp-data`` directory::

    cd comp-data

Inside you can find the following files:

* ``comp_pheno.ped`` - the pedigree file for all families included into the database

* ``instruments`` - directory, containing all instruments

* ``instruments/i1.csv`` - all measurements for instrument ``i1``

* ``comp_pheno_data_dictionary.tsv`` - descriptions for all measurements

* ``comp_pheno_regressions.conf`` - regression configuration file

To import the phenotype data, you can use the ``simple_pheno_import.py`` tool. It will import
the phenotype database directly to the DAE data directory specified in your environment:

.. code::

    simple_pheno_import.py \
        -p comp_pheno.ped \
        -d comp_pheno_data_dictionary.tsv \
        -i instruments/ \
        -o comp_pheno \
        --regression comp_pheno_regressions.conf

Options used in this command are as follows:

* ``-p`` specifies the pedigree file

* ``-d`` specifies the name of the data dictionary file for the phenotype database

* ``-i`` specifies the directory where the instruments are located

* ``-o`` specifies the name of the output phenotype database that will be used in the Phenotype Browser

* ``--regression`` specifies the path to the pheno regression config, describing a list of measures to make regressions against

You can use the ``-h`` option to see all options supported by the tool.

Configure Phenotype Database
++++++++++++++++++++++++++++

Phenotype databases have a short configuration file which points
the system to their files, as well as specifying additional properties.
When importing a phenotype database through the
``simple_pheno_import.py`` tool, a configuration file is automatically
generated. You may inspect the ``gpf_test/pheno/comp_pheno/comp_pheno.conf``
configuration file generated from the import tool:

.. code::

    [vars]
    wd = "."

    [phenotype_data]
    name = "comp_pheno"
    dbfile = "%(wd)s/comp_pheno.db"
    browser_dbfile = "%(wd)s/browser/comp_pheno_browser.db"
    browser_images_dir = "%(wd)s/browser/images"
    browser_images_url = "/static/comp_pheno/browser/images/"

    [regression.age]
    instrument_name = "i1"
    measure_name = "age"
    display_name = "Age"
    jitter = 0.1

    [regression.iq]
    instrument_name = "i1"
    measure_name = "iq"
    display_name = "Non verbal IQ"
    jitter = 0.1

Configure Phenotype Browser
+++++++++++++++++++++++++++

To demonstrate how a study is configured with a phenotype database, we will
be working with the already imported ``comp_all`` study.

The phenotype databases can be attached to one or more studies and/or datasets.
If you want to attach the ``comp_pheno`` phenotype
database to the ``comp_all`` study, you need to specify it in the study's
configuration file, which can be found at ``gpf_test/studies/comp_all/comp_all.conf``.

Add the following line at the beginning of the file, outside of any section:

.. code::

    phenotype_data = "comp_pheno"

To enable the :ref:`phenotype_browser_ui`, add this line:

.. code::

    phenotype_browser = true

After this, the beginning of the configuration file should look like this:

.. code::

    id = "comp_all"
    conf_dir = "."
    has_denovo = true
    phenotype_browser = true
    phenotype_data = "comp_pheno"

When you restart the server, you should be
able to see the 'Phenotype Browser' tab in the `comp_all` study.

Configure Family Filters in Genotype Browser
+++++++++++++++++++++++++++++++++++++++++++++++

A study or a dataset can have phenotype filters configured for its :ref:`genotype_browser_ui`
when it has a phenotype database attached to it. The configuration looks like this:

.. code::

    [genotype_browser]
    enabled = true
    
    family_filters.sample_continuous_filter.name = "Sample Filter Name"
    family_filters.sample_continuous_filter.from = "phenodb"
    family_filters.sample_continuous_filter.source_type = "continuous"
    family_filters.sample_continuous_filter.filter_type = "multi"
    family_filters.sample_continuous_filter.role = "prb"

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

.. code::

    [genotype_browser]
    (...)

    selected_pheno_column_values = ["pheno"]

    pheno.pheno.name = "Measures"
    pheno.pheno.slots = [
        {role = "prb", source = "i1.age", name = "Age"},
        {role = "prb", source = "i1.iq", name = "Iq"}
    ]

For the phenotype columns to be in the Genotype Browser table preview or download file, 
they have to be present in the ``preview_columns`` or the ``download_columns`` in the Genotype Browser
configuration. Add this in the genotype_browser section:

.. code::

    preview_columns = ["family", "variant", "genotype", "effect", "weights", "mpc_cadd", "freq", "pheno"]


Enabling the Phenotype Tool
+++++++++++++++++++++++++++

To enable the :ref:`phenotype_tool_ui` for a study, you must edit
the study's configuration file and set the appropriate property, as with
the :ref:`phenotype_browser_ui`. Open the configuration file ``comp_all.conf``
and add the following line:

.. code::

    phenotype_tool = true

After editing, it should look like this:

.. code::

    id = "comp_all"
    conf_dir = "."
    has_denovo = true
    phenotype_browser = true
    phenotype_data = "comp_pheno"
    phenotype_tool = true


Restart the GPF web server and select the ``comp_all`` study.
You should see the :ref:`phenotype_tool_ui` tab. Once you have selected it, you
can select a phenotype measure of your choice. To get the tool to acknowledge
the variants in the ``comp_all`` study, select the `All` option of the
`Present in Parent` field. Since the effect types of the variants in the comp
study are only `Missense` and `Synonymous`, you may wish to de-select the
`LGDs` option under the `Effect Types` field. There are is also the option to
normalize the results by one or two measures configured as regressors - age and
non-verbal IQ.

Click on the `Report` button to produce the results.

