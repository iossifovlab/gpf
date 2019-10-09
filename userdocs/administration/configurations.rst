System Configuration
====================

Common configuration information
--------------------------------

For parsing all of the system configurations we use
`ConfigParser <https://docs.python.org/3/library/configparser.html>`_. All of
the configurations follows the general INI format for which you can see more
`here <https://docs.python.org/3/library/configparser.html#supported-ini-file-structure>`_.
In all configuration files you can add ``[DEFAULT]`` section which is supported
by the ``ConfigParser``.

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
