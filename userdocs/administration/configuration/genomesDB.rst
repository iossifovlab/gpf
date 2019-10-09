.. _genomes_db:

GenomesDB configuration
=======================

This file is responsible for configuring which reference genomes and gene
models are available to the GPF system and which it should use by default.

Example Configuration
---------------------

.. code-block:: ini

  [genomes]
  defaultGenome = GATK_ResourceBundle_5777_b37_phiX174

  [genome.GATK_ResourceBundle_5777_b37_phiX174]
  chrAllFile = %(wd)s/genomes/GATK_ResourceBundle_5777_b37_phiX174/chrAll.fa

  defaultGeneModel = RefSeq2013

  geneModel.RefSeq2013.file = %(wd)s/genomes/GATK_ResourceBundle_5777_b37_phiX174/refGene-201309.gz
  geneModel.RefSeq.file = %(wd)s/genomes/GATK_ResourceBundle_5777_b37_phiX174/refGene-20190211.gz
  geneModel.CCDS.file = %(wd)s/genomes/GATK_ResourceBundle_5777_b37_phiX174/ccds-201309.gz
  geneModel.knownGene.file = %(wd)s/genomes/GATK_ResourceBundle_5777_b37_phiX174/knownGene-201309.gz
  geneModel.RefSeqMito.file = %(wd)s/genomes/GATK_ResourceBundle_5777_b37_phiX174/refGeneMito-201309.gz

  [PARs]
  regions.X = X:60001-2699520,X:154931044-155260560
  regions.Y = Y:10001-2649520,Y:59034050-59363566

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
