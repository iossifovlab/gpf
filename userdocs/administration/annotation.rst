Annotation Infrastructure
=========================

Annotation is an essential step in any genomic analysis. It is the process of 
assigning attributes or properties to a set of objects that an analyst studies.
For example, one can annotate the genetic variants identified in a group of 
case and control individuals in a genetic study with a prediction of 
pathogenicity of the variants and estimates for the conservation at the 
loci of the variants.

GPF has a well-developed infrastructure for annotation of genetic variants.
Annotation is carried out when importing studies into the system or through the use of CLI tools.
This document will explain how to configure and utilize the annotation infrastructure.

Pipeline configuration
**********************

A series of annotations (performed by annotators) is called a "pipeline".
Pipelines are defined through configuration files in the YAML format, in the form
of a list of annotators. Each annotator can be additionally configured depending on its type.

Annotators can be written as so:

.. code:: yaml

    - <annotator type>: 
        setting 1: value
        setting 2: other value
        ...

Some attributes are general and some are annotator specific.
General ones include: attributes and input_annotatable

Syntax shortcuts are available, such as:

.. code:: yaml

    - <annotator type> 
  
or

.. code:: yaml 

    - <annotator type>: <resource id>
    
These short forms however lack the ability to configure the annotator's settings.

Preamble
********

Other than a list of annotators, annotation configs can also have a preamble section that
holds additional information about the pipeline useful for both human readers and documentation tools.

Below is an example of a pipeline config with a preamble section.
Note that the annotators must be placed in a ``annotators`` section if a preamble is added.

.. code:: yaml

    preamble:
        summary: phyloP hg38 annotation
        description: Annotates with all available HG38 phyloP scores.
        input_reference_genome: hg38/genomes/GRCh38-hg38
        metadata:
            author: Me
            customField: "The metadata section can hold arbitrary key/value pairs - you can put anything here."
            customField2: someCustomValue
            customNestedDictionary:
                key1: value1
    annotators:
        - position_score: hg38/scores/phyloP100way
        - position_score: hg38/scores/phyloP30way
        - position_score: hg38/scores/phyloP20way
        - position_score: hg38/scores/phyloP7way

Annotators
**********

This is a list of all available annotators and their settings in the GPF system.


Annotator settings
##################

=================  ========  ======
Setting            Purpose   Values
=================  ========  ======
resource_id
genome
gene_models
chain
target_genome
input_gene_list
=================  ========  ======

Annotator attributes
####################

=================  ========  ======
Setting            Purpose   Values
=================  ========  ======
source
name
destination
internal
input_annotatable
value_transform
=================  ========  ======

Position score
##############

Annotate with a position score resource.

.. code:: yaml

    - position_score:
        resource_id: <position score resource ID>
        attributes:
        - source: <source score ID>
          name: <destination attribute name>
          position_aggregator: <aggregator to use for INDELs>


NP score
########

Annotate with a nucleotide polymorphism score resource.

.. code:: yaml

    - np_score:
        resource_id: <NP-score resource ID>
        attributes:
        - source: <source score ID>
          name: <destination attribute name>
          position_aggregator: <aggregator to use for INDELs>

Allele score
############

Annotate with an allele score resource.

.. code:: yaml

    - allele_score:
        resource_id: <allele score resource ID>
        attributes:
        - source: <source score ID>
          name: <destination attribute name>


Effect annotator
################

Predicts the variant's effect on proteins (i.e. missense, synonymous, LGD, etc.).

.. code:: yaml

    - effect_annotator: 
        genome: <reference genome resource ID>
        gene_models: <gene models resource ID>


Normalize allele annotator
##########################

.. code:: yaml

    - normalize_allele_annotator:
        genome: hg38/genomes/GRCh38-hg38


Liftover annotator
##################

Lifts over a variant from one reference genome to another.
The product is an "annotatable" (an object annotators can work on) in the target reference genome.
This produced annotatable can then be passed to other annotators using the ``input_annotatable`` setting.

.. code:: yaml

    - liftover_annotator:
        chain: liftover/hg38ToHg19
        target_genome: hg19/genomes/GATK_ResourceBundle_5777_b37_phiX174
        attributes:
        - source: liftover_annotatable
          name: hg19_annotatable
          internal: true


Gene score annotator
####################

.. code:: yaml

  - gene_score_annotator:
    resource_id: <gene score resource ID>
    input_gene_list: <Gene list to use to match variants (see below)>
    attributes:
    - source: <source score ID>
      name: <destination attribute name>
      gene_aggregator: <aggregator type>


.. note:: 

    Input gene list is a list of genes that **must** be present in the annotation context.

    Gene lists are produced by the effect annotator, therefore gene score annotation is
    dependent on an effect annotator being present earlier in the pipeline.

    Effect annotators currently provide two gene lists - ``gene_list`` and ``LGD_gene_list``.


Gene set annotator
##################

TODO


Command line tools
******************

Three annotation tools are provided with GPF - ``annotate_columns``, ``annotate_vcf`` and ``annotate_schema2_parquet``.
Each of these handles a different format, but apart from some differences in the arguments that can be passed, they work in a similar way.
Across all three, input data and a pipeline configuration file are the mandatory arguments that must be provided.
Additionally, a number of optional arguments exist, which can be used to modify much of the behaviour of these tools.

All three tools are capable of parallelizing their workload, and will attempt to do so by default.

Also provided is the ``annotate_doc`` tool, which produces a human-readable HTML document from a given pipeline configuration.
The purpose of this HTML document is to display the pipeline in an easy-to-read layout.

Notes on usage
##############

- When parallelizing is used, a directory for storing task flags and task logs will be created in your working directory. If you wish to re-run the annotation, it is necessary to remove this directory as the flags inside it will prevent the tasks from running.
- The option to reannotate data is provided. This is useful when you wish to modify only specific columns of an already annotated piece of data - for example to update a score column whose score resource has received a new version.
  To carry this out in the ``annotate_columns`` and ``annotate_vcf`` tools, you will have to use to provide the old annotation pipeline through the ``--reannotate`` flag. For ``annotate_schema2_parquet``, this is done automatically, as the annotation pipeline is stored in its metadata.

annotate_columns
################

This tool is used to annotate DSV (delimiter-separated values) formats - CSV, TSV, etc. It expects a header to be provided, from which it will attempt to identify relevant columns - chromosome, position, reference, alternative, etc.
If the file has been indexed using Tabix, the tool will parallelize its workload by splitting it into tasks by region size.

Example usage of annotate_columns
+++++++++++++++++++++++++++++++++

.. code:: bash

    $ annotate_columns.py input.tsv annotation.yaml

Options for annotate_columns
++++++++++++++++++++++++++++

.. runblock:: console

    $ annotate_columns --help

annotate_vcf
############

This tool is used to annotate files in the VCF format.
If the file has been indexed using Tabix, the tool will parallelize its workload by splitting it into tasks by region size.

Example usage of annotate_vcf
+++++++++++++++++++++++++++++

.. code:: bash

    $ annotate_vcf.py input.vcf.gz annotation.yaml

Options for annotate_vcf
++++++++++++++++++++++++

.. runblock:: console

    $ annotate_vcf --help

annotate_schema2_parquet
########################

This tool is used to annotate Parquet datasets partitioned according to GPF's ``schema2`` format. It expects a directory of the dataset as input.
The tool will always parallelize the annotation, unless explicitly disabled using the ``-j 1`` argument.

Unlike the other tools, reannotation will be carried out automatically if a previous annotation is detected in the dataset.

Example usage of annotate_schema2_parquet
+++++++++++++++++++++++++++++++++++++++++

.. code:: bash

    $ annotate_schema2_parquet.py input_parquet_dir annotation.yaml

Options for annotate_schema2_parquet
++++++++++++++++++++++++++++++++++++

.. runblock:: console

    $ annotate_schema2_parquet --help

annotate_doc
############

Produce an HTML file describing the provided pipeline.

Example usage of annotate_doc
+++++++++++++++++++++++++++++

.. code:: bash

    $ annotate_doc.py annotation.yaml

Options for annotate_doc
++++++++++++++++++++++++

.. runblock:: console

    $ annotate_doc --help


Example annotations
*******************

How to annotate variants with `ClinVar`
#######################################

For this example, we'll assume that you have a GRR repository with the ClinVar score resource.
We'll use a small list of de Novo variants saved as ``denovo-variants.tsv``:

.. code-block::

    CHROM   POS	      REF    ALT  person_ids
    chr14   21403214  T      C    f1.p1
    chr14   21431459  G      C    f1.p1
    chr14   21391016  A      AT   f2.p1
    chr14   21403019  G      A    f2.p1
    chr14   21402010  G      A    f3.p1
    chr14   21393484  TCTTC  T    f3.p1


Let us create an annotation configuration stored as ``clinvar-annotation.yaml``:

.. code:: yaml

    - allele_score: clinvar_20221105


Run the ``annotate_columns`` tool:

.. code-block:: bash

    annotate_columns --grr ./grr_definition.yaml \
        --col_pos POS --col_chrom CHROM --col_ref REF --col_alt ALT \
        denovo-variants.tsv clinvar_annotation.yaml


How to annotate with gene score annotators
##########################################

Preparing a variants file
+++++++++++++++++++++++++

For this example we will reuse the ``denovo_variants.tsv`` in the previous example:

.. code-block::

    CHROM   POS       REF    ALT  person_ids
    chr14   21403214  T      C    f1.p1
    chr14   21431459  G      C    f1.p1
    chr14   21391016  A      AT   f2.p1
    chr14   21403019  G      A    f2.p1
    chr14   21402010  G      A    f3.p1
    chr14   21393484  TCTTC  T    f3.p1


Setting up the Genomic Resource Repository
++++++++++++++++++++++++++++++++++++++++++

We will be using the SFARI gene score along with a genome and gene models
from the `public GRR <https://grr.seqpipe.org>`_. Create a ``grr_definition.yaml``
that looks like this:

  .. code-block:: yaml

    type: group
    children:
    - id: "seqpipe"
      type: "url"
      directory: "https://grr.seqpipe.org"


Setting up the annotation configuration
+++++++++++++++++++++++++++++++++++++++

Create a ``properties-annotation.yaml`` like this:

  .. code-block:: yaml

    - effect_annotator:
        gene_models: hg38/gene_models/refSeq_v20200330
        genome: hg38/genomes/GRCh38-hg38
    - gene_score_annotator:
        resource_id: gene_properties/gene_scores/SFARI_gene_score
        input_gene_list: gene_list
        attributes:
        - source: "SFARI gene score"
          name: SFARI_gene_score

As mentioned before, when setting up gene score annotators, we need to have a gene list in the annotation context.
The gene list is provided by the effect annotator preceding the gene score annotator.

Annotating the variants
+++++++++++++++++++++++

Run the ``annotate_columns`` tool:

.. code-block:: bash

    annotate_columns --grr ./grr_definition.yaml \
        --col_pos POS --col_chrom CHROM --col_ref REF --col_alt ALT \
        denovo-variants.tsv properties_annotation.yaml


Gene score annotator with changed aggregator
############################################

.. code:: yaml

    - effect_annotator:
        gene_models: hg38/gene_models/refSeq_v20200330
        genome: hg38/genomes/GRCh38-hg38       
    
    - gene_score_annotator:
        resource_id: gene_properties/gene_scores/pLI
        input_gene_list: gene_list
        attributes:
        - source: pLI
          gene_aggregator: max


Simple position score annotation
################################

.. code:: yaml

    - position_score: hg38/scores/phyloP7way


Effect annotator with default resources
#######################################

.. code:: yaml

    - position_score: hg38/scores/phyloP7way
    - effect_annotator

This effect annotator will use the reference genome and gene models from the active GPF instance or from CLI parameters such as:

.. code::

    --ref hg38/genomes/GRCh38-hg38 --genes hg38/gene_models/refSeq_v20200330


Large annotation with various annotators
########################################

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
          name: hg19_annotatable
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

    - allele_score:
        resource_id: hg38/variant_frequencies/gnomAD_v2.1.1_liftover/exomes
        input_annotatable: normalized_allele

    - allele_score:
        resource_id: hg38/variant_frequencies/gnomAD_v2.1.1_liftover/genomes
        input_annotatable: normalized_allele

    - allele_score:
        resource_id: hg38/variant_frequencies/gnomAD_v3/genomes
        input_annotatable: normalized_allele