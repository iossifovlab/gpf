GPF Instance Configuration
==========================

* ``instance_id`` - ID of the GPF instance.


* ``reference_genome`` - reference genome resource ID to be used by the GPF
  instance. This is a required field.

* ``gene_models`` - gene models resource ID to be used by the GPF instance.
  This is a required field.

* ``annotation`` - annotation configuration.
  This could be a path to a configuration file or a list of annotators.

* ``grr`` - genomic resources repository configuration.

* ``gene_scores_db`` - list of gene scores to be used by the GPF instance.

* ``gene_sets_db`` - list of gene sets to be used by the GPF instance.


* ``default_study_config`` - default study configuration. This is a path to a
  configuration file.

* ``studies`` - directory where the study configuration files are located.
  If not specified, the GPF instance will look in ``studies`` subdirectory in
  the GPF instance directory.

* ``datasets`` - directory where the dataset configuration files are located.
  If not specified, the GPF instance will look in ``datasets`` subdirectory in
  the GPF instance directory.

* ``phenotype_data`` - directory where the phenotype data configuration files are
  located. If not specified, the GPF instance will look in ``pheno``
  subdirectory in the GPF instance directory.

* ``gene_profiles_config`` - gene profiles configuration. This is a path to a
  configuration file.


* ``genotype_storage`` - genotype storage configurations.

* ``phenotype_storage`` - phenotype storage configurations.

* ``cache_path`` - path to the cache directory. This is a path to a directory where
  the GPF instance will store the cache files.

* ``phenotype_images`` 

* ``gpfjs``


.. code-block:: yaml

  vars:
    instance_id: data_hg38_local
  
  instance_id: '%(instance_id)s'
  
  reference_genome:
    resource_id: hg38/genomes/GRCh38-hg38
  
  gene_models:
    resource_id: hg38/gene_models/refGene_v20170601
  
  gene_sets_db:
    gene_set_collections:
    - gene_properties/gene_sets/autism
    - gene_properties/gene_sets/relevant
    - gene_properties/gene_sets/sfari
    - gene_properties/gene_sets/spark
    - gene_properties/gene_sets/MSigDB_curated
    - gene_properties/gene_sets/miRNA
    - gene_properties/gene_sets/GO
    - gene_properties/gene_sets/PFAM_37.0_domains
    - gene_properties/gene_sets/miRNA_Darnell
  
  gene_scores_db:
    gene_scores:
    - gene_properties/gene_scores/LGD
    - gene_properties/gene_scores/RVIS
    - gene_properties/gene_scores/pLI
    - gene_properties/gene_scores/pRec
    - gene_properties/gene_scores/SFARI_gene_score
    - gene_properties/gene_scores/Satterstrom_Buxbaum_Cell_2020
    - gene_properties/gene_scores/Iossifov_Wigler_PNAS_2015
    - gene_properties/gene_scores/LOEUF
  
  annotation:
    conf_file: annotation.yaml
  
  phenotype_data:
    dir: pheno
  
  studies:
    dir: studies
  
  datasets:
    dir: datasets
  
  default_study_config:
    conf_file: defaultConfiguration.conf
  
  gene_profiles_config:
    conf_file: geneProfiles.yaml
    
  gpfjs:
    visible_datasets:
    - ALL_genotypes
    - SSC_genotypes
    - SPARK_genotypes
  
  genotype_storage:
    default: duckdb_parquet
    storages:

    - id: duckdb_parquet
      storage_type: duckdb_parquet
      base_dir: '%($DUCKDB_STORAGE)s/parquet'
      memory_limit: 12GB

    - id: genotype_impala
      storage_type: impala
      read_only: false
      hdfs:
        base_dir: /user/%(instance_id)s/studies
        host: localhost
        port: 8020
        replication: 1
      impala:
        db: '%(instance_id)s'
        hosts:
        - localhost
        port: 21050
        pool_size: 3
  