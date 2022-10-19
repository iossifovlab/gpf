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
        gene_models: hg38/gene_models/refSeq_v20200330
        genome: hg38/genomes/GRCh38-hg38       


Example 3
#########

.. code:: yaml

    - position_score: hg38/scores/phyloP7way 
    - effect_annotator

This one will use the reference genome from the genomic context. The
genomic context can an active gpf_instance or command line parameters like:

.. code::

    -ref hg38/genomes/GRCh38-hg38 -genes hg38/gene_models/refSeq_v20200330



Example 4
#########

.. code:: yaml

    - position_score: hg38/scores/phyloP100way
    - position_score: hg38/scores/phyloP30way
    - position_score: hg38/scores/phyloP20way
    - position_score: hg38/scores/phyloP7way

    - position_score: hg38/scores/phastCons100way
    - position_score: hg38/scores/phastCons30way
    - position_score: hg38/scores/phastCons20way
    - position_score: hg38/scores/phastCons7way

    - np_score: hg38/scores/CADD_v1.4

    - liftover_annotator:
        chain: liftover/hg38ToHg19
        target_genome: hg19/genomes/GATK_ResourceBundle_5777_b37_phiX174
        attributes:
        - source: liftover_annotatable
        destination: hg19_annotatable
        internal: true

    - position_score:
        resource_id: hg19/scores/FitCons-i6-merged
        input_annotatable: hg19_annotatable

    - position_score:
        resource_id: hg19/scores/Linsight
        input_annotatable: hg19_annotatable

    - position_score:
        resource_id: hg19/scores/FitCons2_E067
        input_annotatable: hg19_annotatable

    - position_score:
        resource_id: hg19/scores/FitCons2_E068
        input_annotatable: hg19_annotatable

    - position_score:
        resource_id: hg19/scores/FitCons2_E069
        input_annotatable: hg19_annotatable

    - position_score:
        resource_id: hg19/scores/FitCons2_E070
        input_annotatable: hg19_annotatable

    - position_score:
        resource_id: hg19/scores/FitCons2_E071
        input_annotatable: hg19_annotatable

    - position_score:
        resource_id: hg19/scores/FitCons2_E072
        input_annotatable: hg19_annotatable

    - position_score:
        resource_id: hg19/scores/FitCons2_E073
        input_annotatable: hg19_annotatable

    - position_score:
        resource_id: hg19/scores/FitCons2_E074
        input_annotatable: hg19_annotatable

    - position_score:
        resource_id: hg19/scores/FitCons2_E081
        input_annotatable: hg19_annotatable

    - position_score:
        resource_id: hg19/scores/FitCons2_E082
        input_annotatable: hg19_annotatable

    - np_score:
        resource_id: hg19/scores/MPC
        input_annotatable: hg19_annotatable

    - normalize_allele_annotator:
        genome: hg38/genomes/GRCh38-hg38

    - allele_score:
        resource_id: hg38/variant_frequencies/SSC_WG38_CSHL_2380
        # input_annotatable: normalized_allele

    - allele_score: 
        resource_id: hg38/variant_frequencies/gnomAD_v2.1.1_liftover/exomes
        input_annotatable: normalized_allele

    - allele_score: 
        resource_id: hg38/variant_frequencies/gnomAD_v2.1.1_liftover/genomes
        input_annotatable: normalized_allele

    - allele_score: 
        resource_id: hg38/variant_frequencies/gnomAD_v3/genomes
        input_annotatable: normalized_allele
        



Annotables 
**********

Genomic Position
#################

VCF Variant
#################

Genomic Region
#################

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