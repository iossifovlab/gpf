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


Annotator attribute fields
##########################

These are the fields that can be set when configuring an annotator's attributes.

=================  ================
Setting            Description
=================  ================
source             String. The source from which to take the attribute.
name               String. How the attribute will be labeled in the output annotation.
destination        String. Deprecated variation of ``name``.
internal           Boolean. Whether to discard the attribute when writing the output file. Useful for temporary attributes used to calculate other attributes.
input_annotatable  String. What annotatable object to use instead of the default one read from the input. Used with liftover and normalize allele annotators.
value_transform    String. Python function to evaluate on each value of the attribute. Examples: ``len(value)``, ``value / 10``, etc.
=================  ================

Score annotators
################

The attributes of these annotators generally follow the pattern below:

.. code:: yaml

    - source: <source score ID>
      name: <destination attribute name>

The available scores are those configured in the resource used with the score annotator.
``source`` is the ID of the score as it is configured in its resource, and ``name`` is how it will be labeled in the output annotation.


Aggregators
+++++++++++

- mean
- median
- max
- min
- mode
- join (i.e., join(;))
- list
- dict
- concatenate


Position score
++++++++++++++

Annotate with a position score resource.

.. code:: yaml

    - position_score:
        resource_id: <position score resource ID>
        attributes:
        - source: <source score ID>
          name: <destination attribute name>
          position_aggregator: <aggregator to use for INDELs>


NP score
++++++++

Annotate with a nucleotide polymorphism score resource.

.. code:: yaml

    - np_score:
        resource_id: <NP-score resource ID>
        attributes:
        - source: <source score ID>
          name: <destination attribute name>
          position_aggregator: <aggregator to use for INDELs>
          nucleotide_aggregator: <aggregator to use for NPs>

Allele score
++++++++++++

Annotate with an allele score resource.

.. code:: yaml

    - allele_score:
        resource_id: <allele score resource ID>
        attributes:
        - source: <source score ID>
          name: <destination attribute name>
          position_aggregator: <aggregator to use for INDELs>
          allele_aggregator: <aggregator to use for alleles>


Effect annotator
################

Predicts the variant's effect on proteins (i.e. missense, synonymous, LGD, etc.).
The attributes the annotator will output are the following:

worst_effect
  The worst effect across all transcripts.


gene_effects
  Effect types for each gene.


effect_details
  Effect details for each affected transcript.


gene_list
  List of all genes


LGD_gene_list
  List of all LGD genes


.. code:: yaml

    - effect_annotator:
        genome: <reference genome resource ID>
        gene_models: <gene models resource ID>


Liftover annotator
##################

Lifts over a variant from one reference genome to another.
The product is an "annotatable" (an object annotators can work on) in the target reference genome.
This produced annotatable is labeled ``liftover_annotatable`` and can be passed to other annotators using the ``input_annotatable`` setting.

.. code:: yaml

    - liftover_annotator:
        chain: liftover/hg38ToHg19
        source_genome: hg38/genomes/GRCh38-hg38
        target_genome: hg19/genomes/GATK_ResourceBundle_5777_b37_phiX174
        attributes:
        - source: liftover_annotatable
          name: hg19_annotatable
          internal: true


Normalize allele annotator
##########################

Normalize an allele using the algorithm defined here:
https://genome.sph.umich.edu/wiki/Variant_Normalization

Similar to the liftover annotator, produces an "annotatable" object called ``normalized_allele``.

.. code:: yaml

    - normalize_allele_annotator:
        genome: hg38/genomes/GRCh38-hg38


Gene score annotator
####################

Annotate a variant with a gene score.

.. code:: yaml

  - gene_score_annotator:
    resource_id: <gene score resource ID>
    input_gene_list: <gene list to use to match variants (see below)>
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

Used to annotate whether a variant belongs to a certain gene set.

.. code:: yaml

  - gene_set_annotator:
      resource_id: <gene set collection resource ID>
      gene_set_id: <gene set id>
      input_gene_list: <gene list to use to match variants>


VEP annotators
##############

There are two annotators which depend on and use the Ensembl Variant Effect Predictor (VEP).

Setting up
++++++++++
Using the Ensembl VEP annotators requires the `gpf_vep_annotator` conda package to be installed.

.. code-block:: bash

    mamba install \
        -c conda-forge \
        -c bioconda \
        -c iossifovlab \
        -c defaults \
        gpf_vep_annotator


VEP Full Annotator
++++++++++++++++++
Using the full VEP annotator requires a VEP cache to be accessible in the local file system.

Downloading the VEP cache is done with the `vep_install` tool provided by the `ensembl-vep`
conda package, which comes with `gpf_vep_annotator`.

Download the cache for hg38.

.. code-block:: bash

    vep_install -a cf -s homo_sapiens -y GRCh38 -c /output/path/to/cache --convert

The annotator configuration looks like this:

.. code:: yaml

    - vep_full_annotator:
        cache_dir: <VEP cache directory>

VEP Effect Annotator
++++++++++++++++++++
The VEP effect annotator uses genome and gene model resources to produce
its output with VEP. It needs to have a genomic resource repository with the genome
and gene models prepared.

.. code:: yaml

    - external_vep_gtf_annotator:
        genome: hg38/genomes/GRCh38-hg38
        gene_models: hg38/gene_models/MANE/1.3

Output Attributes
+++++++++++++++++
The two VEP annotators can output the following attributes:

gene
  Gene symbol reported by VEP

gene_id
  Gene ID reported by VEP

feature
  VEP feature

feature_type
  VEP feature type

consequence
  VEP effect type

location
  VEP location

allele
  VEP allele

cdna_position
  VEP cDNA position

cds_position
  VEP cds position

protein_position
  VEP protein position

amino_acids
  Amino acids reported by VEP

codons
  Codons reported by VEP

existing_variation
  Existing variation reported by VEP

impact
  Variant impact reported by VEP

distance
  Distance reported by VEP

strand
  Variant impact reported by VEP

symbol_source
  VEP gene symbol source

worst_consequence
  Worst consequence reported by VEP

highest_impact
  Highest impact reported by VEP

gene_consequence
    List of gene consequence pairs reported by VEP


By default, only the following are produced: `gene`, `feature`, `feature_type`,
`consequence`, `worst_consequence`, `highest_impact`, `gene_consequence`.

The VEP annotators can be run only in batch mode.



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
- The option to allow repeated attributes is provided with the ``--allow-repeated-attributes`` (short form ``-ar``) flag.
  With this flag, the annotation pipeline will append the annotator ID (typically ``A<index of annotator in the pipeline config>)``, e.g. ``A0``, ``A1``) to the attribute's name.
  For example, a repeating attribute called ``my_score`` will appear in the output as ``my_score_A0``, ``my_score_A1``, and so on.

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

    CHROM   POS	      REF    ALT
    chr14   21403214  T      C
    chr14   21431459  G      C
    chr14   21391016  A      AT
    chr14   21403019  G      A
    chr14   21402010  G      A
    chr14   21393484  TCTTC  T

.. note::

    The example variants can be downloaded from here:
    :download:`denovo-variants.tsv <annotation_files/denovo-variants.tsv>`.


Let us create an annotation configuration stored as ``clinvar-annotation.yaml``:

.. code:: yaml

    - allele_score: hg38/scores/clinvar_20221105


Run the ``annotate_columns`` tool:

.. code-block:: bash

    annotate_columns --grr ./grr_definition.yaml \
        --col_pos POS --col_chrom CHROM --col_ref REF --col_alt ALT \
        denovo-variants.tsv clinvar_annotation.yaml


How to annotate with gene score annotators
##########################################

For this example we will reuse the ``denovo_variants.tsv`` from the previous example.

Create an ``annotation.yaml`` config with the following contents:

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

Next, run the ``annotate_columns`` tool:

.. code-block:: bash

    annotate_columns --grr ./grr_definition.yaml \
        --col_pos POS --col_chrom CHROM --col_ref REF --col_alt ALT \
        denovo-variants.tsv annotation.yaml


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


How to annotate with gene set annotators
########################################

.. code:: yaml

    - effect_annotator:
        gene_models: hg38/gene_models/refSeq_v20200330
        genome: hg38/genomes/GRCh38-hg38
    - gene_set_annotator:
        resource_id: gene_properties/gene_sets/autism
        gene_set_id: autism candidates from Iossifov PNAS 2015
        input_gene_list: gene_list


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


Liftover annotation
###################

.. code:: yaml

    - position_score: hg38/scores/phyloP100way

    - liftover_annotator:
        chain: liftover/hg38ToHg19
        source_genome: hg38/genomes/GRCh38-hg38
        target_genome: hg19/genomes/GATK_ResourceBundle_5777_b37_phiX174
        attributes:
        - source: liftover_annotatable
          name: hg19_annotatable
          internal: true

    - position_score:
        resource_id: hg19/scores/FitCons-i6-merged
        input_annotatable: hg19_annotatable
