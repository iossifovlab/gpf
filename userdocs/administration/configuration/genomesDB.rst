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

The default genome to use. The genome id
must reference a configured genome from one of
the ``[genome.<genome id>]`` sections below.

[genome.<genome id>]
--------------------

This section contains information about a single genome.

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

The default gene model to use. This id
must reference a defined gene model from one of the
``geneModel.<gene model id>.file`` properties below.

geneModel.<gene model id>.file
______________________________

.. code-block:: ini

  geneModel.<gene model id>.file = <gene model filename>

This property defines a gene model. It sets both the id of
the gene model and the absolute path to its file. The id
can be chosen by the user.


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
