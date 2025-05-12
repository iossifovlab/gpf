Getting Started with Gene Profiles
##################################

The Gene Profile tool provides summary statistics of the
data managed by GPF and additional relevant information
organized by gene.

To enable the Gene Profile tool, you need to create a configuration for
the tool and add it to the GPF instance configuration file.

Let us create a configuration for the Gene Profile tool in the GPF instance
directory ``minimal_instance/gene_profiles.yaml`` wit the following content:

.. literalinclude:: getting_started_files/gene_profiles.yaml
    :linenos:
    :language: yaml

There are several sections in this configuration file:

- ``datasets``: This section defines the studies and datasets that will be
  used to collect variants statistics. In our example we are going to use
  the ``ssc_denovo`` study - see lines 2-33.

  - For each study or dataset we should define what type of variant statistics
    we want to collect. In our example we are going to collect three types of
    statistics:

    - Count of LGDs de Novo variants for eash gene - lines 4-9;
    - Count of missense de Novo variants for each gene - lines 10-16;
    - Count of intronic INDEL variants for each gene - lines 17-26.

  - For each study or dataset we should define how to split individuals into
    groups. In our example we are going to split them into tow groups -
    ``affected`` and ``unaffected`` - lines 27-33.

- ``gene_scores``: This section defines groups of gene scores that will be used
  in gene profiles. The gene profiles will include score values for each gene
  from the defined gene scores. In our example we are going to use to groups of
  gene scores:

  - ``autism_scores`` - lines 36-42;
  - ``protectsion_scores`` - lines 44-52.

  Please note that all gene scores used in this configuration section should
  be defined in the GPF instance configuration file.

- ``gene_sets``: This section defines groups of gene sets that will be used
  in gene profiles. The gene profiles will show if the gene is included in
  the defined gene sets. In our example we are going to use one group of gene
  sets:

  - ``autism_gene_sets`` - lines 54-67;

    Please note that all gene sets used in this configuration section should
    be defined in the GPF instance configuration file.

- ``gene_links``: This section defines links to internal and external tools
  that contain information aboun genes. In our example we are defining three
  links:
  - lines 70-71 - link to the GPF Gene Browser tools;
  - lines 73-74 - link to the GeneCards site;
  - lines 75-76 - link to the SFARI Gene site.

Once we have this configuration we need to add it to the GPF instance
configuration:

.. code-block:: yaml
    :linenos:
    :emphasize-lines: 28-29

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

    gene_profiles_config:
      conf_file: gene_profiles.yaml




The gene models we are using in our example ``hg38/gene_models/MANE/1.3``
have 19,285 genes. By default the ``generate_gene_profiles`` command will
generate profiles for all genes in the gene models. Please note, that this
command will take a while to finish. On a MacBook Pro M1 with 32GB of RAM
it took about 10 minutes to finish.

.. code-block:: bash

    generate_gene_profile


.. note::

    If you want to speed up the process of generating gene profiles, you can
    limit the number of genes for which the profiles will be generated.

    .. code-block:: bash

        generate_gene_profile \
            --genes \
            CHD8,NCKAP1,DSCAM,ANK2,GRIN2B,SYNGAP1,ARID1B,MED13L,GIGYF1,WDFY3,ANKRD11,DIP2A,TNRC6B,TANC2,TCF7L2,KMT2E,DYRK1A,CHD2,SCN2A,RIMS1

