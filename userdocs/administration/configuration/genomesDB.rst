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

.. FIXME:
  Fill me

.. code-block:: ini

  chrAllFile = <>

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

.. FIXME:
  Fill me

regions.<>
__________

.. FIXME:
  Fill me

.. code-block:: ini

  regions.<> = <comma separated >
