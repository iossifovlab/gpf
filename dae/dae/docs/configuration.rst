configuration package
=====================

Example usage of :mod:`config_parser_base <dae.configuration>`
--------------------------------------------------------------

The following example is how to use
:class:`dae.configuration.dae_config_parser.DAEConfigParser` which inherit
:class:`dae.configuration.config_parser_base.ConfigParserBase`.

.. testcode::

  >>> from dae.configuration.dae_config_parser import DAEConfigParser

.. testsetup::

  >>> import os

  >>> def relative_to_this_test_folder(path):
  ...     return os.path.join(
  ...         os.environ['DAE_SOURCE_DIR'],
  ...         'dae/dae/docs',
  ...         path
  ...     )

  >>> fixtures_dir = relative_to_this_test_folder('fixtures')

Content of the config which will be used in this example is:

  * DAE.conf:

    .. code-block:: ini

      [DEFAULT]
      instance_id = data_hg19_startup

      [storage.genotype_impala]
      type = impala
      impala.host = localhost
      impala.port = 21050
      hdfs.host = localhost
      hdfs.port = 8020
      hdfs.base_dir = /user/%(instance_id)s/studies

      [studiesDB]
      confFile = %(wd)s/studiesDB.conf
      dir = %(wd)s/studies

      [datasetsDB]
      confFile = %(wd)s/datasetsDB.conf
      dir = %(wd)s/datasets

      [genomesDB]
      confFile = %(wd)s/genomesDB.conf

      [genomicScoresDB]
      confFile = %(wd)s/genomicScores.conf

      [annotation]
      confFile = %(wd)s/annotation.conf

      [phenoDB]
      dir = %(wd)s/pheno

      [geneInfoDB]
      confFile = %(wd)s/geneInfo.conf

      [defaultConfiguration]
      confFile = %(wd)s/defaultConfiguration.conf

Read and Parse file configuration
.................................

.. testcode::

  >>> os.environ['DAE_IMPALA_HOST'] = 'impala'

.. testcode::

  >>> config = DAEConfigParser.read_and_parse_file_configuration(
  ...     work_dir=fixtures_dir, environment_override=False
  ... )

.. doctest::

  >>> print(config.storage.genotype_impala.impala.host)
  localhost

  >>> print(config.storage.genotype_impala.impala.port)
  21050

  >>> print(config.storage.genotype_impala.impala.db)
  gpf_variant_db

.. doctest::

  >>> print(config.gpfjs.permission_denied_prompt)
  This is a default permission denied prompt. Please log in or register.

dae.configuration.config_parser_base - module for parsing configuration
-----------------------------------------------------------------------

.. automodule:: dae.configuration.config_parser_base
    :members:
    :undoc-members:
    :show-inheritance:

dae.configuration.dae_config_parser - module for parsing :ref:`DAE Configuration <dae_configuration>`
-----------------------------------------------------------------------------------------------------

.. automodule:: dae.configuration.dae_config_parser
    :members:
    :undoc-members:
    :show-inheritance:
