Getting Started with Gene Sets
##############################

The GPF system provides support for collection of gene symbols of interest
for the analysis of genotype data. There are two types og gene sets that can be
used in GPF:

* de Novo gene sets - for each genotype study that has de Novo variants, the 
  GPF system can create gene sets that contain list of genes with de Novo
  variants of interest; for example, genes with LGSs de Novo variants, genes
  with LGDs de Novo variants in males, etc.

* pre-defined gene sets - these are gene sets that are defined in the GRR used by
  the GPF instance; for example, gene sets in the
  `public GPF Genomic Resources Repository (GRR)
  <https://grr.iossifovlab.com>`_ there multiple gene set collection ready for
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
  this gene set collection contains genes associated with autism;

* `gene_properties/gene_sets/GO_2024-06-17_release
  <https://grr.iossifovlab.com/gene_properties/gene_sets/GO_2024-06-17_release/index.html>`_ -
  this gene set collection contains genes associated with Gene Ontology
  (GO) terms.

To do this, you need to add lines 14-17 to GPF instance configuration file
(``minimal_instance/gpf_instance.yaml``):

.. code-block:: yaml
    :linenos:
    :emphasize-lines: 14-17

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
      - gene_properties/gene_sets/GO_2024-06-17_release

Whe you restart the GPF instance, the configured gene set collections will be
available in the GPF instance user interface. For example, if you navigate to
`Genotype Browser` for ``ssc_denovo`` study,
and select the `Genes > Gene Sets` tab, you will see the configured of gene set
collections.

.. figure:: getting_started_files/ssc_denovo_gene_set_collections.png

   Gene Set Collections in the ``ssc_denovo`` `Genotype Browser` interface

