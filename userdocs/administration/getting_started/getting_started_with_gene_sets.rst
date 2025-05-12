Getting Started with Gene Sets
##############################

The GPF system provides support for the collection of gene symbols of interest
for the analysis of genotype data. There are two types of gene sets that can be
used in GPF:

* de Novo gene sets - for each genotype study that has de Novo variants, the
  GPF system can create gene sets that contain a list of genes with de Novo
  variants of interest; for example, genes with LGSs de Novo variants, genes
  with LGDs de Novo variants in males, etc.

* pre-defined gene sets - these are gene sets that are defined in the GRR used by
  the GPF instance; for example, in the
  `public GPF Genomic Resources Repository (GRR)
  <https://grr.iossifovlab.com>`_ there are multiple gene set collections ready for
  use in the GPF instance.

De Novo Gene Set
++++++++++++++++

By default, for each genotype study with de Novo variants, the GPF system
creates a collection of de Novo gene sets with pre-defined properties. For
example:

* `LGDs` - genes with LGDs de Novo variants;
* `LGDs.Female` - genes with LGDs de Novo variants in females;
* `LGDs.Male` - genes with LGDs de Novo variants in males;
* `Missense` - genes with missense de Novo variants;
* `Missense.Female` - genes with missense de Novo variants in females;
* `Missense.Male` - genes with missense de Novo variants in males;
* etc.

You can use these gene sets in multiple tools in the GPF system. For example,
if you navigate to `Genotype Browser` for ``ssc_denovo`` study,
and select the `Genes > Gene Sets` tab, you will see the list of de Novo gene
sets generated for the study.

.. figure:: getting_started_files/ssc_denovo_denovo_gene_sets.png

   De Novo Gene Sets for ``ssc_denovo`` study

You can use these gene sets in the `Genotype Browser` to filter the variants
in genes that are included in the selected gene set.


Pre-defined Gene Set Collections
++++++++++++++++++++++++++++++++

To add pre-defined gene sets from the GRR to the GPF instance, you need to edit
the GPF instance configuration file (``minimal_instance/gpf_instance.yaml``).

Let's say that we want to add the following gene set collections from the
public GRR:

* `gene_properties/gene_sets/autism
  <https://grr.iossifovlab.com/gene_properties/gene_sets/autism/index.html>`_ -
  autism gene sets derived from publications;

* `gene_properties/gene_sets/relevant
  <https://grr.iossifovlab.com/gene_properties/gene_sets/relevant/index.html>`_ -
  variety of gene sets with potential relevance to autism;

* `gene_properties/gene_sets/GO_2024-06-17_release
  <https://grr.iossifovlab.com/gene_properties/gene_sets/GO_2024-06-17_release/index.html>`_ -
  this gene set collection contains genes associated with Gene Ontology
  (GO) terms.

To do this, you need to add lines 14-18 to the GPF instance configuration file
(``minimal_instance/gpf_instance.yaml``):

.. code-block:: yaml
    :linenos:
    :emphasize-lines: 14-18

    instance_id: minimal_instance

    reference_genome:
      resource_id: "hg38/genomes/GRCh38-hg38"

    gene_models:
      resource_id: "hg38/gene_models/MANE/1.3"

    annotation:
      config:
        - allele_score: hg38/variant_frequencies/gnomAD_4.1.0/genomes/ALL
        - allele_score: hg38/scores/ClinVar_20240730

    gene_sets_db:
      gene_set_collections:
      - gene_properties/gene_sets/autism
      - gene_properties/gene_sets/relevant
      - gene_properties/gene_sets/GO_2024-06-17_release

When you restart the GPF instance, the configured gene set collections will be
available in the GPF instance user interface. For example, if you navigate to
`Genotype Browser` for ``ssc_denovo`` study,
and select the `Genes > Gene Sets` tab, you will see the configured gene set
collections.

.. figure:: getting_started_files/ssc_denovo_gene_set_collections.png

   Gene Set Collections in the ``ssc_denovo`` `Genotype Browser` interface


Pre-defined Gene Scores
+++++++++++++++++++++++

To add pre-defined gene scores from the GRR to the GPF instance, you need to
edit the GPF instance configuration file
(``minimal_instance/gpf_instance.yaml``).

Let's say that we want to add the following gene set collections from the
public GRR:

- `gene_properties/gene_scores/Satterstrom_Buxbaum_Cell_2020
  <https://grr.iossifovlab.com/gene_properties/gene_scores/Satterstrom_Buxbaum_Cell_2020/index.html>`_
  TADA derived gene-autism association score

- `gene_properties/gene_scores/Iossifov_Wigler_PNAS_2015
  <https://grr.iossifovlab.com/gene_properties/gene_scores/Iossifov_Wigler_PNAS_2015/index.html>`_
  Probability of a gene to be associated with autism

- `gene_properties/gene_scores/LGD
  <https://grr.iossifovlab.com/gene_properties/gene_scores/LGD/index.html>`_
  Gene vulnerability/intolerance score based on the rare LGD variants

- `gene_properties/gene_scores/RVIS
  <https://grr.iossifovlab.com/gene_properties/gene_scores/RVIS/index.html>`_
  Residual Variation Intolerance Score

- `gene_properties/gene_scores/LOEUF
  <https://grr.iossifovlab.com/gene_properties/gene_scores/LOEUF/index.html>`_
  Degree of intolerance to predicted Loss-of-Function (pLoF) variation


To do this, you need to add lines 20-26 to the GPF instance configuration file
(``minimal_instance/gpf_instance.yaml``):

.. code-block:: yaml
    :linenos:
    :emphasize-lines: 20-26

    instance_id: minimal_instance

    reference_genome:
      resource_id: "hg38/genomes/GRCh38-hg38"

    gene_models:
      resource_id: "hg38/gene_models/MANE/1.3"

    annotation:
      config:
        - allele_score: hg38/variant_frequencies/gnomAD_4.1.0/genomes/ALL
        - allele_score: hg38/scores/ClinVar_20240730

    gene_sets_db:
      gene_set_collections:
      - gene_properties/gene_sets/autism
      - gene_properties/gene_sets/relevant
      - gene_properties/gene_sets/GO_2024-06-17_release

    gene_scores_db:
      gene_scores:
      - gene_properties/gene_scores/Satterstrom_Buxbaum_Cell_2020
      - gene_properties/gene_scores/Iossifov_Wigler_PNAS_2015
      - gene_properties/gene_scores/LGD
      - gene_properties/gene_scores/RVIS
      - gene_properties/gene_scores/LOEUF

When you restart the GPF instance, the configured gene scores will be
available in the GPF instance user interface. For example, if you navigate to
`Genotype Browser` for ``ssc_denovo`` study,
and select the `Genes > Gene Scores` tab, you will see the configured gene set
collections.

.. figure:: getting_started_files/ssc_denovo_gene_scores.png

   Gene Scores in the ``ssc_denovo`` `Genotype Browser` interface

