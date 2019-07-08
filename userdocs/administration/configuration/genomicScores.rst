Genomic Scores Configuration
============================

This configuration file hosts the list of all available genomic scores
and the properties of their histograms.

[genomicScores]
---------------

dir
###

.. code-block:: ini

  dir = {path to genomic scores histogram file directory}

The absolute path to the directory containing the genomic scores' histogram
files.

scores
######

.. code-block:: ini

  dir = {genomic score name},{genomic score name 2},(...)

A comma-separated list of all available genomic scores.
Every genomic score listed here must have a corresponding section
``genomicScores.{score name}``.

[genomicScores.{score name}]
----------------------------

file
####

.. code-block:: ini

  file = {path to genomic score histogram file}

The absolute path to the score's histogram file.

desc
####

.. code-block:: ini

  desc = {description}

A brief description of the genomic score.

bins
####

.. code-block:: ini

  bins = {amount of bins}

The amount of bins in the score's histogram. The value must be an integer.

yscale
######

.. code-block:: ini

  yscale = {linear / log}

The scale for the Y axis of the score's histogram.
Must be either ``linear`` or ``log``.

xscale
######

.. code-block:: ini

  xscale = {linear / log}

The scale for the X axis of the score's histogram.
Must be either ``linear`` or ``log``.

range
#####

.. code-block:: ini

  range = {min value},{max value}

The range domain of the score - its lowest and largest possible
values separated by a comma.

help_file
#########

.. code-block:: ini

  help_file = {path to help file}

The absolute path to the score's help file in markdown format.
