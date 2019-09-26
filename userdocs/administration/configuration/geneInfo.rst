.. _gene_info_db:

Gene Info Configuration
=======================

This configuration file hosts information about gene data.

[geneInfo]
----------

geneInfoFile
____________

.. code-block:: ini

  geneInfoFile = <TODO>

TODO

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

.. code-block:: ini

  file = <TODO>

TODO

webFormatStr
____________

.. code-block:: ini

  webFormatStr = <TODO>

TODO

webLabel
________

.. code-block:: ini

  webLabel = <TODO>

TODO

[geneWeights]
-------------

This is a optional section containing list of selected gene weights.

geneWeights
___________

.. code-block:: ini

  weights = <gene weight id 1>,<gene weight id 2>,<...>

A comma-separated list of selected gene weights. If this property is missing
then all deffind weights with section name ``[geneWeights.<gene weight id>]``
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

file
____

.. code-block:: ini

  file = <TODO>

TODO
