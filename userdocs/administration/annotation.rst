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


3'UTR_gene_list
  List of all 3'UTR genes


3'UTR-intron_gene_list
  List of all 3'UTR-intron genes


5'UTR_gene_list
  List of all 5'UTR genes


5'UTR-intron_gene_list
  List of all 5'UTR-intron genes


frame-shift_gene_list
  List of all frame-shift genes


intergenic_gene_list
  List of all intergenic genes


intron_gene_list
  List of all intron genes


missense_gene_list
  List of all missense genes


no-frame-shift_gene_list
  List of all no-frame-shift genes


no-frame-shift-newStop_gene_list
  List of all no-frame-shift-newStop genes


noEnd_gene_list
  List of all noEnd genes


noStart_gene_list
  List of all noStart genes


non-coding_gene_list
  List of all non-coding genes


non-coding-intron_gene_list
  List of all non-coding-intron genes


nonsense_gene_list
  List of all nonsense genes


splice-site_gene_list
  List of all splice-site genes


synonymous_gene_list
  List of all synonymous genes


CDS_gene_list
  List of all CDS genes


CNV+_gene_list
  List of all CNV+ genes


CNV-_gene_list
  List of all CNV- genes


coding_gene_list
  List of all coding genes


noncoding_gene_list
  List of all noncoding genes


CNV_gene_list
  List of all CNV genes


LGDs_gene_list
  List of all LGD genes


LGD_gene_list (deprecated)
  List of all LGD genes


nonsynonymous_gene_list
  List of all nonsynonymous genes


UTRs_gene_list
  List of all UTRs genes


.. code:: yaml

    - effect_annotator:
        genome: <reference genome resource ID>
        gene_models: <gene models resource ID>

Specifying the ``genome`` parameter in the configuration is optional - the effect annotator will attempt to get a genome in the following order:

1. ``genome`` parameter in annotator configuration
2. ``reference_genome`` label in provided ``gene_models`` resource's configuration
3. ``input_reference_genome`` field from annotation pipeline config preamble section
4. Genomic context


Simple effect annotator
#######################

Classify an event according to the scheme described in
https://pmc.ncbi.nlm.nih.gov/articles/PMC8410909/figure/Fig2/.
The attributes the annotator will output are the following:

effect
  The worst effect across all transcripts.


genes
  The affected genes.


gene_list
  List of all genes.


.. code:: yaml

    - simple_effect_annotator:
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

Specifying the ``source_genome`` and ``target_genome`` parameters in the configuration is optional - if none are provided, the annotator will attempt to collect them from the provided ``chain`` resource's configuration. Specifically, the ``chain`` resource can have ``source_genome`` and ``target_genome`` labels in its configuration's meta section.

Normalize allele annotator
##########################

Normalize an allele using the algorithm defined here:
https://genome.sph.umich.edu/wiki/Variant_Normalization

Similar to the liftover annotator, produces an "annotatable" object called ``normalized_allele``.

.. code:: yaml

    - normalize_allele_annotator:
        genome: hg38/genomes/GRCh38-hg38
        attributes:
        - source: normalized_allele
          name: hg38_normalized_annotatable
          internal: true


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

Used to annotate whether a variant belongs to gene sets in a gene set collection.

.. code:: yaml

  - gene_set_annotator:
      resource_id: <gene set collection resource ID>
      input_gene_list: <gene list to use to match variants>
      attributes:
        - <gene set name>
        - in_sets


The gene set annotator can output an attribute for every single gene set in a collection
along with a special attribute `in_sets`, which is a list of the names of every gene set
that the variant belongs to from the collection.

SpliceAI annotator plugin
#########################

The SpliceAI annotator plugin is a wrapper around the 
`SpliceAI tool <https://www.cell.com/cell/fulltext/S0092-8674(18)31629-5>`_,
which predicts the effect of variants on splicing.

This annotator produces the following attributes:

delta_score
    SpliceAI variant annotation. These include delta scores (DS) and
    delta positions (DP) for acceptor gain (AG), acceptor loss (AL),
    donor gain (DG), and donor loss (DL). 
    
    Format: `ALLELE|SYMBOL|DS_AG|DS_AL|DS_DG|DS_DL|DP_AG|DP_AL|DP_DG|DP_DL`


To configure the SpliceAI annotator plugin, use the following syntax:

.. code:: yaml

    - spliceai_annotator:
        genome: hg38/genomes/GRCh38-hg38
        gene_models: hg38/gene_models/refSeq_v20200330
        distance: 500
        mask: false

where:

genome
    The reference genome resource ID to use for the annotation.

gene_models
    The gene models resource ID to use for the annotation.

distance
    maximum distance between the variant and gained/lost splice site,
    defaults to 50

mask:
    mask scores representing annotated acceptor/donor gain and
    unannotated acceptor/donor loss, defaults to `false`




VEP annotators
##############

There are two annotators which depend on and use the Ensembl Variant Effect Predictor (VEP) via docker.

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

Using the VEP annotators also requires `Docker` to be setup.

**The VEP annotators can be run only in batch mode.**

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
        vep_version: <VEP version to use>

If `vep_version` is not specified, then the annotator will use the latest docker image available on the
`ensemblorg/ensembl-vep` docker repository. Versions can be specified with and without minor versions.
When specified with only the major version, the minor will be set to .0  

Valid version examples: `113`, `113.0`, `113.3`, `112`, etc.

Full Annotator Output Attributes
++++++++++++++++++++++++++++++++
The full VEP annotator can output the following attributes:

Location
  Location of variant in standard coordinate format (chr:start or chr:start-end)

Allele
  The variant allele used to calculate the consequence

Gene
  Stable ID of affected gene

Feature
  Stable ID of feature

Feature_type
  Type of feature - Transcript, RegulatoryFeature or MotifFeature

Consequence
  Consequence type

cDNA_position
  Relative position of base pair in cDNA sequence

CDS_position
  Relative position of base pair in coding sequence

Protein_position
  Relative position of amino acid in protein

Amino_acids
  Reference and variant amino acids

Codons
  Reference and variant codon sequence

Existing_variation
  Identifier(s) of co-located known variants

IMPACT
  Subjective impact classification of consequence type

DISTANCE
  Shortest distance from variant to transcript

STRAND
  Strand of the feature (1/-1)

FLAGS
  Transcript quality flags

VARIANT_CLASS
  SO variant class

SYMBOL
  Gene symbol (e.g. HGNC)

SYMBOL_SOURCE
  Source of gene symbol

HGNC_ID
  Stable identifer of HGNC gene symbol

BIOTYPE
  Biotype of transcript or regulatory feature

CANONICAL
  Indicates if transcript is canonical for this gene

MANE
  MANE (Matched Annotation from NCBI and EMBL-EBI) set(s) the transcript belongs to

MANE_SELECT
  MANE Select (Matched Annotation from NCBI and EMBL-EBI) Transcript

MANE_PLUS_CLINICAL
  MANE Plus Clinical (Matched Annotation from NCBI and EMBL-EBI) Transcript

TSL
  Transcript support level

APPRIS
  Annotates alternatively spliced transcripts as primary or alternate based on a range of computational methods

CCDS
  Indicates if transcript is a CCDS transcript

ENSP
  Protein identifer

SWISSPROT
  UniProtKB/Swiss-Prot accession

TREMBL
  UniProtKB/TrEMBL accession

UNIPARC
  UniParc accession

UNIPROT_ISOFORM
  Direct mappings to UniProtKB isoforms

GENE_PHENO
  Indicates if gene is associated with a phenotype, disease or trait

SIFT
  SIFT prediction and/or score

PolyPhen
  PolyPhen prediction and/or score

EXON
  Exon number(s) / total

INTRON
  Intron number(s) / total

DOMAINS
  The source and identifer of any overlapping protein domains

miRNA
  SO terms of overlapped miRNA secondary structure feature(s)

HGVSc
  HGVS coding sequence name

HGVSp
  HGVS protein sequence name

HGVS_OFFSET
  Indicates by how many bases the HGVS notations for this variant have been shifted

AF
  Frequency of existing variant in 1000 Genomes combined population

AFR_AF
  Frequency of existing variant in 1000 Genomes combined African population

AMR_AF
  Frequency of existing variant in 1000 Genomes combined American population

EAS_AF
  Frequency of existing variant in 1000 Genomes combined East Asian population

EUR_AF
  Frequency of existing variant in 1000 Genomes combined European population

SAS_AF
  Frequency of existing variant in 1000 Genomes combined South Asian population

gnomADe_AF
  Frequency of existing variant in gnomAD exomes combined population

gnomADe_AFR_AF
  Frequency of existing variant in gnomAD exomes African/American population

gnomADe_AMR_AF
  Frequency of existing variant in gnomAD exomes American population

gnomADe_ASJ_AF
  Frequency of existing variant in gnomAD exomes Ashkenazi Jewish population

gnomADe_EAS_AF
  Frequency of existing variant in gnomAD exomes East Asian population

gnomADe_FIN_AF
  Frequency of existing variant in gnomAD exomes Finnish population

gnomADe_MID_AF
  Frequency of existing variant in gnomAD exomes Mid-eastern population

gnomADe_NFE_AF
  Frequency of existing variant in gnomAD exomes Non-Finnish European population

gnomADe_OTH_AF
  Frequency of existing variant in gnomAD exomes other combined populations

gnomADe_SAS_AF
  Frequency of existing variant in gnomAD exomes South Asian population

gnomADe_REMAINING_AF
  Frequency of existing variant in gnomAD exomes remaining combined populations

gnomADg_AF
  Frequency of existing variant in gnomAD genomes combined population

gnomADg_AFR_AF
  Frequency of existing variant in gnomAD genomes African/American population

gnomADg_AMI_AF
  Frequency of existing variant in gnomAD genomes Amish population

gnomADg_AMR_AF
  Frequency of existing variant in gnomAD genomes American population

gnomADg_ASJ_AF
  Frequency of existing variant in gnomAD genomes Ashkenazi Jewish population

gnomADg_EAS_AF
  Frequency of existing variant in gnomAD genomes East Asian population

gnomADg_FIN_AF
  Frequency of existing variant in gnomAD genomes Finnish population

gnomADg_MID_AF
  Frequency of existing variant in gnomAD genomes Mid-eastern population

gnomADg_NFE_AF
  Frequency of existing variant in gnomAD genomes Non-Finnish European population

gnomADg_OTH_AF
  Frequency of existing variant in gnomAD genomes other combined populations

gnomADg_SAS_AF
  Frequency of existing variant in gnomAD genomes South Asian population

gnomADg_REMAINING_AF
  Frequency of existing variant in gnomAD genomes remaining combined populations

MAX_AF
  Maximum observed allele frequency in 1000 Genomes, ESP and ExAC/gnomAD

MAX_AF_POPS
  Populations in which maximum allele frequency was observed

CLIN_SIG
  ClinVar clinical significance of the dbSNP variant

SOMATIC
  Somatic status of existing variant

PHENO
  Indicates if existing variant(s) is associated with a phenotype, disease or trait; multiple values correspond to multiple variants

PUBMED
  Pubmed ID(s) of publications that cite existing variant

MOTIF_NAME
  The stable identifier of a transcription factor binding profile (TFBP) aligned at this position

MOTIF_POS
  The relative position of the variation in the aligned TFBP

HIGH_INF_POS
  A flag indicating if the variant falls in a high information position of the TFBP

MOTIF_SCORE_CHANGE
  The difference in motif score of the reference and variant sequences for the TFBP

TRANSCRIPTION_FACTORS
  List of transcription factors which bind to the transcription factor binding profile

worst_consequence
  Worst consequence reported by VEP

highest_impact
  Highest impact reported by VEP

gene_consequence
  List of gene consequence pairs reported by VEP


By default, only the following are produced: `SYMBOL`, `Feature`, `Feature_type`,
`Consequence`, `worst_consequence`, `highest_impact`, `gene_consequence`.


VEP Effect Annotator
++++++++++++++++++++
The VEP effect annotator uses genome and gene model resources to produce
its output with VEP. It needs to have a genomic resource repository with the genome
and gene models prepared.

.. code:: yaml

    - external_vep_gtf_annotator:
        genome: hg38/genomes/GRCh38-hg38
        gene_models: hg38/gene_models/MANE/1.3
        vep_version: <VEP version to use>

If `vep_version` is not specified, then the annotator will use the latest docker image available on the
`ensemblorg/ensembl-vep` docker repository. Versions can be specified with and without minor versions.
When specified with only the major version, the minor will be set to .0  

Valid version examples: `113`, `113.0`, `113.3`, `112`, etc.


Effect Annotator Output Attributes
++++++++++++++++++++++++++++++++++
The VEP effect annotator can output the following attributes:

Location
  Location of variant in standard coordinate format (chr:start or chr:start-end)

Allele
  The variant allele used to calculate the consequence

Gene
  Stable ID of affected gene

Feature
  Stable ID of feature

Feature_type
  Type of feature - Transcript, RegulatoryFeature or MotifFeature

Consequence
  Consequence type

cDNA_position
  Relative position of base pair in cDNA sequence

CDS_position
  Relative position of base pair in coding sequence

Protein_position
  Relative position of amino acid in protein

Amino_acids
  Reference and variant amino acids

Codons
  Reference and variant codon sequence

Existing_variation
  Identifier(s) of co-located known variants

IMPACT
  Subjective impact classification of consequence type

DISTANCE
  Shortest distance from variant to transcript

STRAND
  Strand of the feature (1/-1)

FLAGS
  Transcript quality flags

SYMBOL
  Gene symbol (e.g. HGNC)

SYMBOL_SOURCE
  Source of gene symbol

HGNC_ID
  Stable identifer of HGNC gene symbol

SOURCE
  Source of transcript

worst_consequence
  Worst consequence reported by VEP

highest_impact
  Highest impact reported by VEP

gene_consequence
  List of gene consequence pairs reported by VEP

<gene model filename>
  Value from provided gene models


By default, only the following are produced: `SYMBOL`, `Feature`, `Feature_type`,
`Consequence`, `worst_consequence`, `highest_impact`, `gene_consequence` and the
value from the provided gene models.



Running the VEP annotation
++++++++++++++++++++++++++

With a prepared variants file and `annotation.yaml` file, the pipeline can be ran
using `annotate_columns` with the `--batch-mode` flag.

Example `annotate_columns` run:

.. code-block:: bash

   annotate_columns ./variants.tsv.gz ./annotation.yaml -w work -o ./out.tsv -v -j 4 --batch-mode --col-chrom CHROM --col-pos POS --col-ref REF -r 10000 --col-alt ALT --allow-repeated-attributes



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
