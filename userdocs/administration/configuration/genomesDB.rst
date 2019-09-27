.. _genomes_db:

GenomesDB configuration
=======================

This configuration file hosts information for the genome.

[genomes]
---------

defaultGenome
_____________

.. code-block:: ini

  defaultGenome = <default genome id>

The given id belongs to one of the given in the ``[genome.<genome id>]``
section genomes.

[genome.<genome id>]
--------------------

This section contains information about genome.

chrAllFile
__________

.. code-block:: ini

  chrAllFile = <TODO>

TODO

defaultGeneModel
________________

.. code-block:: ini

  defaultGeneModel = <default gene model id>

The given id belongs to one of the given in the
``geneModel.<gene model id>.file`` properties.

geneModel.<gene model id>.file
______________________________

.. code-block:: ini

  geneModel.<gene model id>.file = <gene model filename>

The absolute filepath to the gene model with <gene model id>.


[PARs]
------

TODO

regions.<TODO>
______________

.. code-block:: ini

  regions.<TODO> = <comma separated TODO>

TODO
