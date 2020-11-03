.. _dae_configuration:

DAE Configuration
=================

This is the main configuration file - it lists GPF subsystems in the form of
sections and specifies required parameters, such as the location of a
configuration file and other filesystem paths.

.. note::
  You can use interpolation values when specifying filepaths.

Parser
------

:class:`DAEConfigParser <dae.configuration.dae_config_parser.DAEConfigParser>`
is the parser responsible for reading and parsing this configuration file.

Example Configuration
---------------------

.. code-block:: ini

  [DEFAULT]
  instance_id = data_hg19_startup

  [genotype_storage]
  default = genotype_impala

  [storage.genotype_impala]
  type = impala
  impala.host = localhost
  impala.port = 21050
  impala.db = gpf_variant_db
  hdfs.host = localhost
  hdfs.port = 8020
  hdfs.base_dir = /user/%(instance_id)s/studies

  [storage.genotype_filesystem]
  type = filesystem
  dir = %(wd)s/studies

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
  scores_hg19_dir = /genomic-scores-hg19
  scores_hg38_dir = /genomic-scores-hg38

  [annotation]
  confFile = %(wd)s/annotation.conf

  [phenoDB]
  dir = %(wd)s/pheno

  [geneInfoDB]
  confFile = %(wd)s/geneInfo.conf

  [defaultConfiguration]
  confFile = %(wd)s/defaultConfiguration.conf

  [gpfjs]
  permissionDeniedPrompt = This is a default permission denied prompt. Please log in or register.
  permissionDeniedPromptFile = %(wd)s/permissionDeniedPrompt.md

[genotype_storage]
------------------

default
_______

.. code-block:: ini

  default = <default genotype storage id>

The default genotype storage to use. The genotype storage id must reference a
configured genotype storage from one of the ``[storage.<genotype storage id>]``
sections below.

[storage.<genotype storage id>]

type
____

.. code-block:: ini

  type = <genotype storage type>

Type of the genotype storage. Supported types are impala and filesystem.

impala genotype storage options
_______________________________

impala.host
~~~~~~~~~~~

.. code-block:: ini

  impala.host = <Impala hostname>

ENVIRONMENT OVERRIDE
  ``DAE_IMPALA_HOST``

Hostname of the Impala server.

impala.port
~~~~~~~~~~~

.. code-block:: ini

  impala.port = <Impala port number>

DEFAULT
  .. code-block::
    from dae.configuration.dae_config_parser import DAEConfigParser

    print(f"``{DAEConfigParser.DEFAULT_VALUES['impala.port']}``")

ENVIRONMENT OVERRIDE
  ``DAE_IMPALA_PORT``

Port number of the Impala server.

impala.db
~~~~~~~~~

.. code-block:: ini

  impala.db = <Impala database name>

DEFAULT
  .. code-block::
    from dae.configuration.dae_config_parser import DAEConfigParser

    print(f"``{DAEConfigParser.DEFAULT_VALUES['impala.db']}``")

ENVIRONMENT OVERRIDE
  ``DAE_IMPALA_DB``

Name of the database used by Impala for storing variants and pedigree
information.

hdfs.host
~~~~~~~~~

.. code-block:: ini

  hdfs.host = <HDFS hostname>

ENVIRONMENT OVERRIDE
  ``DAE_HDFS_HOST``

Hostname of the HDFS server.

hdfs.port
~~~~~~~~~

.. code-block:: ini

  hdfs.port = <HDFS port number>

DEFAULT
  .. code-block::
    from dae.configuration.dae_config_parser import DAEConfigParser

    print(f"``{DAEConfigParser.DEFAULT_VALUES['hdfs.port']}``")

ENVIRONMENT OVERRIDE
  ``DAE_HDFS_PORT``

Port number of the HDFS server.

hdfs.base_dir
~~~~~~~~~~~~~

.. FIXME:
  Fill me

.. code-block:: ini

  hdfs.base_dir = <>

DEFAULT
  .. code-block::
    from dae.configuration.dae_config_parser import DAEConfigParser

    print(f"``{DAEConfigParser.DEFAULT_VALUES['hdfs.base_dir']}``")

filessytem genotype storage options
___________________________________

dir
~~~

.. code-block:: ini

  dir = <directory containing studies>

Directory containing studies data.

[studiesDB]
-----------

confFile
________

.. code-block:: ini

  confFile = <studies db config file>

The absolute filepath to the studiesDB configuration file. You can see more
about this configuration :ref:`here <studies_and_datasets_db>`.

dir
___

.. code-block:: ini

  dir = <directory containing studies>

Directory containing studies data. This directory is expected to contain study
configurations. You can see more about study and dataset configurations
:ref:`here <study_and_dataset>`.

[datasetsDB]
------------

confFile
________

.. code-block:: ini

  confFile = <datasets db config file>

The absolute filepath to the datasetsDB configuration file. You can see more
about this configuration :ref:`here <studies_and_datasets_db>`.

dir
___

.. code-block:: ini

  dir = <directory containing datasets>

Directory containing datasets data. This directory is expected to contain
dataset configurations. You can see more about study and dataset configurations
:ref:`here <study_and_dataset>`.

[genomesDB]
-----------

confFile
________

.. code-block:: ini

  confFile = <genomes db config file path>

The absolute filepath to the genomesDB configuration file. You can see
more about this configuration :ref:`here <genomes_db>`.

[genomicScoresDB]
-----------------

confFile
________

.. code-block:: ini

  confFile = <genomic scores db file path>

The absolute filepath to the genomicScoresDB configuration file. You can see
more about this configuration :ref:`here <genomic_scores_db>`.

scores_hg19_dir
_______________

.. code-block:: ini

  scores_hg19_dir = <dir containing HG19 genomic scores>

ENVIRONMENT OVERRIDE
  ``DAE_GENOMIC_SCORES_HG19``

The absolute path to the directory containing the HG19 genomic scores.

scores_hg38_dir
_______________

.. code-block:: ini

  scores_hg38_dir = <dir containing HG38 genomic scores>

ENVIRONMENT OVERRIDE
  ``DAE_GENOMIC_SCORES_HG38``

The absolute path to the directory containing the HG38 genomic scores.

[annotation]
------------

confFile
________

.. code-block:: ini

  confFile = <annotation configuration file path>

The absolute filepath to the annotation configuration file. You can see more
about this configuration :ref:`here <annotation>`.

[phenoDB]
---------

dir
___

.. code-block:: ini

  dir = <phenotype databases directory>

The absolute filepath to the directory containing phenotype databases.
The system will traverse this path and load any INI configuration
files that contain a ``phenoDB`` section. You can see more about phenotype
database configurations :ref:`here <pheno_db>`.

[geneInfoDB]
------------

confFile
________

.. code-block:: ini

  confFile = <gene info db configuration file path>

The absolute filepath to the geneInfoDB configuration file. You can see more
about this configuration :ref:`here <gene_info_db>`.

[defaultConfiguration]
----------------------

confFile
________

.. code-block:: ini

  confFile = <defaultConfiguration file path>

The absolute filepath to the defaultConfiguration file. The configuration in
this file is used as a default configuration for all studies and datasets. You can
see more about this configuration :ref:`here <default_configuration>`.

[gpfjs]
-------

permissionDeniedPromptFile
__________________________

.. code-block:: ini

  permissionDeniedPromptFile = <absolute filepath to markdown file>

The absolute filepath to the permissionDeniedPromptFile file. This file
contains markdown to display in the browser when access is denied to a user.
The content of this file is stored in permissionDeniedPrompt.

permissionDeniedPrompt
______________________

.. code-block:: ini

  permissionDeniedPrompt = <markdown>

DEFAULT
  .. code-block::
    from dae.configuration.dae_config_parser import DAEConfigParser

    print(f"``{DAEConfigParser.DEFAULT_SECTION_VALUES['gpfjs']['permissionDeniedPrompt']}``")

The markdown to display in the browser when access to a user is denied. If
permissionDeniedPromptFile is defined, this property is overridden with the
file content from the given path.
