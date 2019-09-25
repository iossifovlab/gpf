DAE Configuration
=================

This is the main configuration file - it lists GPF subsystems in the form of
sections and specifies required parameters, such as the location of a
configuration file and other filesystem paths.

.. note::
  You can use interpolation values when specifying filepaths.


[HDFS]
------

host
____

.. code-block:: ini

  host = {HDFS hostname}

ENVIRONMENT OVERRIDE
  ``DAE_HDFS_HOST``

Hostname of the HDFS server.

port
____

.. code-block:: ini

  port = {HDFS port number}

DEFAULT
  .. exec::
    from dae.configuration.dae_config_parser import DAEConfigParser

    print(f"``{DAEConfigParser.DEFAULT_SECTION_VALUES['HDFS']['port']}``")

ENVIRONMENT OVERRIDE
  ``DAE_HDFS_PORT``

Port number of the HDFS server.

baseDir
_______

.. code-block:: ini

  baseDir = {TODO}

DEFAULT
  .. exec::
    from dae.configuration.dae_config_parser import DAEConfigParser

    print(f"``{DAEConfigParser.DEFAULT_SECTION_VALUES['HDFS']['baseDir']}``")

TODO

[Impala]
--------

host
____

.. code-block:: ini

  host = {Impala hostname}

ENVIRONMENT OVERRIDE
  ``DAE_IMPALA_HOST``

Hostname of the Impala server.

port
____

.. code-block:: ini

  port = {Impala port number}

DEFAULT
  .. exec::
    from dae.configuration.dae_config_parser import DAEConfigParser

    print(f"``{DAEConfigParser.DEFAULT_SECTION_VALUES['Impala']['port']}``")

ENVIRONMENT OVERRIDE
  ``DAE_IMPALA_PORT``

Port number of the Impala server.

db
__

.. code-block:: ini

  db = {Impala database name}

DEFAULT
  .. exec::
    from dae.configuration.dae_config_parser import DAEConfigParser

    print(f"``{DAEConfigParser.DEFAULT_SECTION_VALUES['Impala']['db']}``")

ENVIRONMENT OVERRIDE
  ``DAE_IMPALA_DB``

Name of the database used by Impala for storing variants and pedigree
information.

[studiesDB]
-----------

confFile
________

.. code-block:: ini

  confFile = {TODO}

dir
___

.. code-block:: ini

  dir = {directory containing studies}

Directory containing studies data. This directory is expected to contain study
configurations. You can see more about study and dataset configurations
:ref:`here <study_and_dataset>`.

[datasetsDB]
------------

confFile
________

.. code-block:: ini

  confFile = {TODO}

dir
___

.. code-block:: ini

  dir = {directory containing datasets}

Directory containing datasets data. This directory is expected to contain
dataset configurations. You can see more about study and dataset configurations
:ref:`here <study_and_dataset>`.

[genomesDB]
-----------

confFile
________

.. code-block:: ini

  confFile = {genomes db config file path}

The absolute filepath to the genomesDB configuration file. You can see
more about this configuration :ref:`here <genomes_db>`.

dir
___

.. code-block:: ini

  dir = {TODO}

[genomicScoresDB]
-----------------

confFile
________

.. code-block:: ini

  confFile = {genomic scores db file path}

The absolute filepath to the genomicScoresDB configuration file. You can see
more about this configuration :ref:`here <genomic_scores_db>`.

dir
___

.. code-block:: ini

  dir = {TODO}

scores_hg19_dir
_______________

.. code-block:: ini

  scores_hg19_dir = {dir containing hg19 genomic scores}

ENVIRONMENT OVERRIDE
  ``DAE_GENOMIC_SCORES_HG19``

The absolute dirpath to the hg19 genomic scores.

scores_hg38_dir
_______________

.. code-block:: ini

  scores_hg38_dir = {dir containing hg38 genomic scores}

ENVIRONMENT OVERRIDE
  ``DAE_GENOMIC_SCORES_HG38``

The absolute dirpath to the hg38 genomic scores.

[annotation]
------------

confFile
________

.. code-block:: ini

  confFile = {annotation file path}

The absolute filepath to the annotation configuration file. You can see more
about this configuration :ref:`here <annotation>`.

dir
___

.. code-block:: ini

  dir = {TODO}

[phenoDB]
---------

dir
___

.. code-block:: ini

  dir = {phenotype databases directory}

The absolute filepath to the directory containing phenotype databases.
The system will traverse this path and load any INI configuration
files that contain a ``phenoDB`` section. You can see more about phenotype
database configurations :ref:`here <pheno_db>`.

[geneInfoDB]
------------

confFile
________

.. code-block:: ini

  confFile = {gene info db file path}

The absolute filepath to the geneInfoDB configuration file. You can see more
about this configuration :ref:`here <gene_info_db>`.

dir
___

.. code-block:: ini

  dir = {TODO}

[defaultConfiguration]
----------------------

confFile
________

.. code-block:: ini

  confFile = {defaultConfiguration file path}

The absolute filepath to the defaultConfiguration file. The configuration in
this file is used as default configuration for studies and datasets. You can
see more about this configuration :ref:`here <default_configuration>`.

[gpfjs]
-------

permissionDeniedPromptFile
__________________________

.. code-block:: ini

  permissionDeniedPromptFile = {the markdown filepath}

The absolute filepath to the permissionDeniedPromptFile file. This file
contains markdown to show in gpfjs when access is denied to a user. Content of
this file is loaded to permissionDeniedPrompt.

permissionDeniedPrompt
______________________

.. code-block:: ini

  permissionDeniedPrompt = {the markdown string}

DEFAULT
  .. exec::
    from dae.configuration.dae_config_parser import DAEConfigParser

    print(f"``{DAEConfigParser.DEFAULT_SECTION_VALUES['gpfjs']['permissionDeniedPrompt']}``")

The markdown to show in gpfjs when access to a user is denied. If
permissionDeniedPromptFile is defined in the same section of configuration,
this property is overridden with the file content from the given path.
