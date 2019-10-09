.. _genomic_scores_db:

Genomic Scores Configuration
============================

This configuration file hosts the list of all available genomic scores
and the properties of their histograms.

Example Configuration
---------------------

.. code-block:: ini

  [genomicScores]
  scores = mpc,cadd_gs_raw

  [genomicScores.mpc]
  id = mpc
  file = %(wd)s/genomicScores/mpc
  desc = MPC - Missense badness, PolyPhen-2, and Constraint
  bins = 100
  yscale = log
  xscale = linear
  range = 0,1

  [genomicScores.cadd_gs_raw]
  id = cadd_gs_raw
  file = %(wd)s/genomicScores/cadd_raw_gs
  desc = CADD GS raw
  bins = 101
  yscale = log
  xscale = linear
  help_file = %(wd)s/genomicScores/cadd_raw_gs.md

  [genomicScores.cadd_gs_phred]
  id = cadd_gs_phred
  file = %(wd)s/genomicScores/cadd_phred_gs
  desc = CADD GS phred
  bins = 101
  yscale = log
  xscale = linear
  help_file = %(wd)s/genomicScores/cadd_phred_gs.md

[genomicScores]
---------------

This is a optional section containing list of selected genomic score.

scores
______

.. code-block:: ini

  scores = <genomic score id 1>,<genomic score id 2>,<...>

A comma-separated list of selected genomic scores. If this property is missing
then all defined scores in this file are selected.

[genomicScores.<score id>]
----------------------------

id
__

.. code-block:: ini

  id = <genomic score identifier>

Identifier of the genomic score. Default value is <score id> from the score
section.

file
____

.. code-block:: ini

  file = <path to genomic score histogram file>

The absolute path to the score's histogram file.

desc
____

.. code-block:: ini

  desc = <description>

A brief description of the genomic score.

bins
____

.. code-block:: ini

  bins = <amount of bins>

The amount of bins in the score's histogram. The value must be an integer.

yscale
______

.. code-block:: ini

  yscale = <linear / log>

The scale for the Y axis of the score's histogram.

xscale
______

.. code-block:: ini

  xscale = <linear / log>

The scale for the X axis of the score's histogram.

range
_____

.. code-block:: ini

  range = <<min value>,<max value>>

The range domain of the score - its lowest and largest possible values
separated by a comma.

help_file
_________

.. code-block:: ini

  help_file = <path to help file>

The absolute path to the score's help file in markdown format.
