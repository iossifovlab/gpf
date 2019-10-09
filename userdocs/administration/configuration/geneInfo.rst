.. _gene_info_db:

Gene Info Configuration
=======================

.. FIXME:
  Extend Gene Info Configuration description.

This file is responsible for configuring which gene info information, gene
terms, gene weights and chromosomes are available to the GPF system.

Example Configuration
---------------------

.. code-block:: ini

  [geneInfo]
  geneInfoFile = %(wd)s/geneInfo/humanGeneInfo.txt

  [geneTerms.main]
  file = %(wd)s/geneInfo/GeneSets
  webFormatStr = key| (|count|): |desc
  webLabel = Main

  [geneTerms.GO]
  file = %(wd)s/geneInfo/GO-map.txt
  webFormatStr = key| (|count|): |desc
  webLabel = GO Terms

  [geneWeights]
  weights = LGD_rank,pLI

  [geneWeights.LGD_rank]
  file = %(wd)s/geneInfo/GeneWeights/LGD.csv
  desc = LGD rank
  bins = 150
  yscale = linear
  xscale = linear
  range = 1,10000

  [geneWeights.LGD_score]
  file = %(wd)s/geneInfo/GeneWeights/LGD.csv
  desc = LGD score
  bins = 150
  yscale = log
  xscale = linear

  [geneWeights.pLI]
  file = %(wd)s/geneInfo/GeneWeights/ExAC.csv
  desc = ExAC pLI
  bins = 150
  yscale = log
  xscale = log

  [chromosomes]
  file = %(wd)s/geneInfo/hgTables.txt

[geneInfo]
----------

geneInfoFile
____________

.. FIXME:
  Fill me

.. code-block:: ini

  geneInfoFile = <>

[geneTerms.<gene term id>]
--------------------------

id
__

.. code-block:: ini

  id = <gene term identifier>

Identifier of the gene term. Default value is <gene term id> from the
``[geneTerms.<gene term id>]`` section name.

file
____

.. FIXME:
  Fill me

.. code-block:: ini

  file = <>

webFormatStr
____________

.. FIXME:
  Fill me

.. code-block:: ini

  webFormatStr = <>

webLabel
________

.. FIXME:
  Fill me

.. code-block:: ini

  webLabel = <>

[geneWeights]
-------------

This is an optional section containing a list of selected gene weights.

weights
_______

.. code-block:: ini

  weights = <gene weight id 1>,<gene weight id 2>,<...>

A comma-separated list of selected gene weights. If this property is missing,
then all defined weights with section name ``[geneWeights.<gene weight id>]``
in this file are selected.

[geneWeights.<gene weight id>]
------------------------------

id
__

.. code-block:: ini

  id = <gene weight identifier>

Identifier of the gene weight. Default value is <gene weight id> from the
``[geneWeights.<gene weight id>]`` section name.

file
____

.. code-block:: ini

  file = <path to gene weight histogram file>

The absolute path to the gene weight's histogram file.

desc
____

.. code-block:: ini

  desc = <description>

A brief description of the gene weight.

bins
____

.. code-block:: ini

  bins = <amount of bins>

The amount of bins in the gene weight's histogram. The value must be an
integer.

yscale
______

.. code-block:: ini

  yscale = <linear / log>

The scale for the Y axis of the gene weight's histogram.

xscale
______

.. code-block:: ini

  xscale = <linear / log>

The scale for the X axis of the gene weight's histogram.

range
______

.. code-block:: ini

  range = <<min value>,<max value>>

The range domain of the gene weight - its lowest and largest possible values
separated by a comma.

[chromosomes]
-------------

.. FIXME:
  Fill me

file
____

.. code-block:: ini

  file = <>
