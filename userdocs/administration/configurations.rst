System Configuration
====================

Common configuration information
--------------------------------

For parsing all of the system configurations we use
slightly modified version of `ConfigParser <https://docs.python.org/3/library/configparser.html>`_
which you can find :ref:`here <case_sensitive_config_parser>`. All of the
configurations follows the general INI format for which you can see more
`here <https://docs.python.org/3/library/configparser.html#supported-ini-file-structure>`_.
In all configuration files you can add ``[DEFAULT]`` section which is supported
by the ``ConfigParser``.

You can use interpolation values when specifying filepaths. You can use for
this purpose ``work_dir`` and ``wd`` which are added by a parsers to all of the
configurations as default values for all of the sections. Path of the
``work_dir`` and ``wd`` is the same is the path to the directory containing the
configuration file.

Common documentation information
--------------------------------

Within the configuration documentation, some properties have miscellaneous
information about them defined below the property signature. This information
can be about entries such as default values and environment overrides.
Currently, there are:

  * ``DEFAULT`` - This information option defines default value of the property
    which is set in the code.

  * ``ENVIRONMENT OVERRIDE`` - This information option defines name of the
    environment variable which can override property from the configuration.

.. toctree::
   :maxdepth: 2

   configuration/dae
   configuration/studies_and_datasets_db_configuration
   configuration/genomesDB
   configuration/genomicScores
   configuration/annotation
   configuration/pheno
   configuration/regression
   configuration/geneInfo
   configuration/defaultConfiguration
   configuration/study_and_dataset_configuration
   configuration/allowed_values
