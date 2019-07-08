DAE Configuration
=================

This is the main configuration file - it lists GPF subsystems in the
form of sections and specifies required parameters, such as
the location of a configuration file and other filesystem paths.

.. note:: 
  You can use interpolation values when specifying filepaths.

[studiesDB]
-----------

confFile
########

dir
###

[datasetsDB]
------------

confFile
########

dir
###

[genomesDB]
-----------

confFile
########

dir
###

[genomicScoresDB]
-----------------

confFile
########

dir
###

scores_hg19_dir
###############

scores_hg38_dir
###############

[annotation]
------------

confFile
########

dir
###

[phenoDB]
---------

dir
###

.. code-block:: ini

  dir = {phenotype databases directory}

The absolute filepath to the directory containing phenotype databases.
The system will traverse this path and load any INI configuration
files that contain a ``phenoDB`` section.

[geneInfoDB]
------------

confFile
########

dir
###

[enrichment]
------------

confFile
########

[defaultConfiguration]
----------------------

confFile
########

.. code-block:: ini

  confFile = {defaultConfiguration file path}

The absolute filepath to the defaultConfiguration file.
