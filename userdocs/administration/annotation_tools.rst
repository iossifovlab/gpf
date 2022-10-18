Annotation
==========


Introduction
************

   

Example 1
#########

.. code:: yaml

    - position_score: hg38/scores/phyloP7way 


Example 2
#########

.. code:: yaml

    - position_score: hg38/scores/phyloP7way 
    - effect_annotator: 
        gene_models: hg38/GRCh38-hg38/gene_models/refSeq_20200330 
        genome: hg38/GRCh38-hg38/genome 


Example 3
#########

.. code:: yaml

    - position_score: hg38/scores/phyloP7way 
    - effect_annotator


Annotation pipeline
*******************

General structure
#################

The pipeline is a yaml file that to the top level is a list with annotators.
Each annotator looks like:

.. code:: yaml

    - <annotator type>: 
        A1: v1
        A2: v2
        ...

There are syntax sort cuts possible, like

.. code:: yaml

    - <annotator type> 
  
or

.. code:: yaml 

    - <annotator type>: <resource id>
    
Some attributes are general and some are annotator specific. 
General ones include: attributes and input_annotatable


Position score
++++++++++++++

.. code:: yaml

    - position_score:
        resource_id: <position score resource ID>
        attributes:
        - source: <source score ID>
          destination: <destination attribute name>
          position_aggregator: <aggregator to use for INDELs>


NP score
++++++++

.. code:: yaml

    - np_score:
        resource_id: <NP-score resource ID>
        attributes:
        - source: <source score ID>
          destination: <destination attribute name>
          position_aggregator: <aggregator to use for INDELs>

Allele score
++++++++++++

.. code:: yaml

    - allele_score:
        resource_id: <allele score resource ID>
        attributes:
        - source: <source score ID>
          destination: <destination attribute name>


Effect annotator
++++++++++++++++


.. code:: yaml

    - effect_annotator: 
        genome: <reference genome resource ID>
        gene_models: <gene models resource ID>


Normalize allele annotator
++++++++++++++++++++++++++

.. code:: yaml

    - normalize_allele_annotator:
        genome: hg38/genomes/GRCh38-hg38


Lift-over annotator
+++++++++++++++++++


.. code:: yaml

    - liftover_annotator:
        chain: liftover/hg38ToHg19
        target_genome: hg19/genomes/GATK_ResourceBundle_5777_b37_phiX174
        attributes:
        - source: liftover_annotatable
        destination: hg19_annotatable
        internal: true


Gene score annotator
++++++++++++++++++++


ClinVar annotator
+++++++++++++++++


Command Line Tools
*******************

annotate_columns


annotate_vcf