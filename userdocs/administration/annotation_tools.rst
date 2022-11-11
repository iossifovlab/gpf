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


Example: How to use VCF INFO annotator to annotate variants with `ClinVar`
**************************************************************************

.. note:: 

    Input files for this example can be downloaded from 
    `clinvar-annotation.tar.gz <https://iossifovlab.com/distribution/public/clinvar-annotation.tar.gz>`_.


Let us have a small list of de Novo variants saved into ``denovo-variants.tsv``:

.. code-block::

    CHROM   POS	      REF    ALT  person_ids
    chr14   21403214  T      C    f1.p1
    chr14   21431459  G      C    f1.p1
    chr14   21391016  A      AT   f2.p1
    chr14   21403019  G      A    f2.p1
    chr14   21402010  G      A    f3.p1
    chr14   21393484  TCTTC  T    f3.p1


Prepare the ``ClinVar`` resource
################################

First, let us prepare the ClinVar resource.

* Download the resource from https://www.ncbi.nlm.nih.gov/clinvar/
* Since our variants are in a small region of chr14 let us get a subset of 
  ClinVar to work with. Use ``bcftools`` to get a region 
  chr14:10000000-30000000 from the ClinVar resource:

  .. code-block:: bash

    bcftools view -o clinvar_20221105_chr14_10000000_30000000.vcf.gz -O z \
        -r 14:10000000-30000000 clinvar_20221105.vcf.gz

* Since chromosomes names in ClinVar in GRCh38 reference genome are without
  ``chr`` prefix, we need to rename them. Use ``bcftools annotate`` command
  to rename them. First create a ``chr14_rename.txt`` file that describes
  mapping of chromosome `14` name to `chr14`:

  .. code-block:: bash

    14 chr14

  and run the ``bcftools annotate`` command:

  .. code-block:: bash

    bcftools annotate --rename-chrs chr14_rename \
        clinvar_20221105_chr14_10000000_30000000.vcf.gz

  and tabix the resulting file:

  .. code-block:: bash

    tabix -p vcf clinvar_20221105_chr14_10000000_30000000.vcf.gz

Prepare local Genomic Resources Repository (GRR)
################################################

* Create a directory named ``local_repo``:
  
  .. code-block:: bash

    mkdir local_repo
    cd local_repo

* Turn this directory into a GRR repository using ``grr_manage``:
  
  .. code-block:: bash

    grr_manage init

* Create a directory for the ``ClinVar`` resource:
  
  .. code-block:: bash

    mkdir clinvar_20221105_chr14_10000000_30000000
    cd clinvar_20221105_chr14_10000000_30000000

* Copy ClinVar VCF file and tabix index into this directory:
  
  .. code-block:: bash

    cp <path to ClinVar VCFs>/clinvar_20221105_chr14_10000000_30000000.vcf.gz* .

* Create a genomic resource configuration file ``genomic_resource.yaml``:
  
  .. code-block:: yaml

    type: vcf_info
    
    filename: clinvar_20221105_chr14_10000000_30000000.vcf.gz
    index_filename: clinvar_20221105_chr14_10000000_30000000.vcf.gz.tbi
    
    desc: |
      Fragment from the ClinVar resource downloaded at 20221105.
    
    scores:
    
    - id: AF_ESP
      type: float
      desc: allele frequencies from GO-ESP
    
    - id: AF_EXAC
      type: float
      desc: allele frequencies from ExAC
    
    - id: AF_TGP
      type: float
      desc: allele frequencies from TGP
    
    - id: ALLELEID
      type: int
      desc: the ClinVar Allele ID
    
    - id: CLNDN
      type: str
      desc: |
        ClinVar's preferred disease name for the concept specified by disease 
        identifiers in CLNDISDB
    
    - id: CLNDNINCL
      type: str
      desc: |
        For included Variant : ClinVar's preferred disease name for the concept 
        specified by disease identifiers in CLNDISDB
    
    - id: CLNDISDB
      type: str
      desc: Tag-value pairs of disease database name and identifier, e.g. OMIM:NNNNNN

    ...

* Create the manifest file and update the contents of the ``local_repo`` using 
  ``grr_manage``:

  .. code-block:: bash

    grr_manage repo-repair

* Create a ``grr_definition.yaml`` file that points to the ``local_repo``:
  
  .. code-block:: yaml

    id: "local"
    type: group
    children:
    - id: "local_repo"
      type: "directory"
      directory: <path to local_repo>/local_repo

* Use ``grr_browse`` to check that ``clivar_20221105_chr14_10000000_30000000``
  is available:

  .. code-block:: bash

    grr_browse -g grr_definition.yaml

  with similar to the following output:

  .. code-block:: bash

    vcf_info             0        3       417014 clinvar_20221105_chr14_10000000_30000000


Annotate variants with ClinVar resource
#######################################

Let us create an annotation configuration stored into 
``clinvar-annotation.yaml``:

.. code:: yaml
    
    - vcf_info: clinvar_20221105_chr14_10000000_30000000


Run ``annotate_columns`` tool:

.. code-block:: bash

    annotate_columns -grr ./grr_definition.yaml \
        --col_pos POS --col_chrom CHROM --col_ref REF --col_alt ALT \
        denovo-variants.tsv clinvar_annotation.yaml

