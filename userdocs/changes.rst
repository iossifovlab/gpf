Release Notes
=============

* 2024.10.1
    * Bump Angular version to 17
    * Bump DuckDb version to 1.1.1
    * Fix Impala genotype storage bugs
    * Clean up dataset statistics unit tests

* 2024.10.0
    * Bump Angular version to 16
    * Clean up of GPFjs code
    * Fix annotatoion pipeline documentation links to genomic resources
    * Support for full VEP annotation in VEP annotator plugin
    * Reorganization of de Novo gene sets API

* 2024.9.3
    * Fix phenotype measures download in phenotype browser
    * Fix searches for datasets in management user interface
    * Fix datasets permissions REST API

* 2024.9.2
    * Support search for datasets in management user interface
    * Fix denovo report generation
    * Remove duplicated large and small value labes in genomic scores histograms help modals
    * Fix bigWig genomic position table fetch method
    * Fix inmemory genomic position table handling of zero based scores
    * Fix handling of displayed_values_percent in categorical histograms
  
* 2024.9.1
    * Fix default number of bins in genomic scores histograms
    * Support case insensitive search in phenotype browser
    * Update links to annotators documentation in annotation pipeline documentation
    * Add missing files method in gene sets genomic resource implementation
    * Fix handling of ultra rare heuristics in DuckDb genotype storage queries
    * Clean up and imporements in wdae unit testing
    * Fix hanlding of zero based scores in inmemory genomic position table
    * Fix phenotype browser table sorting buttons state
    * Refactor and clean up of GPFjs internal state handling and transition to ngrx

* 2024.9.0
    * Performance improvements in annotation with bigWig scores resources
    * Bug fixing in wdae datasets API hierarchy
    * Phenotype data import type inference improvements
    * GPF validation runner error reporting improvements
    * BigWig genomic resources buffering Improvments
    * Phenotype data import of browser data improvements
    * Phenotype browser table improvements
    * Support for integer region bins in schema2 genotype storages
    * Schema2 Parquet loader fixes in hadling of regions
    * DuckDb genotype storage reorganization
    * Support for DuckDb genotype storage over S3
    * Separate GPF federation into a package ``gpf_federation``
    * Revisit histogram configuration and support for user defined plot functions
    * Improvements in ``gpf_wdae`` unit testing

* 2024.8.2
    * Improvement of SQL query builder for family and summary variants in
      DuckDb genotype storage
    * Fix packaging of external VEP annotator plugin
    * Support for serialisation of  additional attributes of family variants
    * Fix support for log-scale Y axis in categorical histograms
    * Fix loading of gene profiles search term from gene profiles state
* 2024.8.1
    * Fix caching of genotype data groups descriptions
    * Genomic position table optimization for bigWig resources
* 2024.8.0
    * Fix for pheno data import on clusters
    * Fix genomic scores histograms large and small value labels
    * Change genomic scores configuration to support `column_name` and `column_index`
    * Fix support for genomic scores with `zero_based` genomic position table
* 2024.7.8
    * Fix handling of bigWig resources with chromosome mapping in `grr_manage`

* 2024.7.7
    * Added unit tests for external VEP annotator plugin
    * Fix collection of study parents in `gpf_wdae`
    * Fix bigWig genomic position table fetch method
    * Fix annotation pipeline preamble
    * Fix gene browser input field behavior in GPFjs
    * Fix query cancelation on destroy of component in GPFjs

* 2024.7.6
    * Added web caching for GPF instance home and about pages
    * Fix handling of permissions for `any_user`` group in `gpf_wdae`
    * Fix gene profiles single gene search from home page
    * Clean up old dataset description cache in GPFjs
    * Fix search query cancelation in phenotype browser
    * Fix handling of description for annonymous users in GPFjs
    * Fix in dataset selector dropdown in GPFjs

* 2024.7.5
    * Performance improvements in calculation of access rights for datasets
    * Fixes in datasets routing in GPFjs
    * Added UI for resetting gene profiles state

* 2024.7.4
    * Fixes in pheno measures dropdown selector for genotype browser and pheno
      tool


* 2024.7.3
    * Bump versions of django dependencies
    * Fix handling of phenotype data groups
    * Fix sorting of pheno browser table
    * Gene profiles user interface state store in user profile
    * Improvement in enrichment tool results display
    * Fixes in `gpf_validation_runner` tool
    * Fixes for serialization of gene models in GTF format
    * Fix chromosome mapping for bigWig genomic position table
    * Fix in phenotype tool user interface controls
    * Fix in gene browser user interface coding only control
    * Fix in histogram sliders user interface
    * Fixes for handling of selected dataset in GPFjs internal state
    * New pheno measures dropdown selector for genotype browser and pheno tool


* 2024.7.2
    * Tool for drawing score resources histograms `draw_score_histograms`
    * Gene sets clean up and fixes
    * Fix handling of internal buffer of tabix genomic position table


* 2024.7.1
    * Improvements in genomic position table performance
    * Initial support for 0-based genomic scores in genomic position table
    * Initial support for serialization of gene models in GTF format
    * Fix in handling of saved queries in GPFjs

* 2024.7.0
    * Bump Python version to 3.11
    * Fix in gene profiles search for genes
    * Support for browser caching of GPF wdae requests
    * Support for style tag in GRR info pages resource description
    * Support for ZSTD compression of variants data blobs in schema2 parquet
    * Fixes in annotation pipeline construction
    * Fixes in support for bigWig format in genomic scores
    * Fixes in handling of selected dataset in GPFjs
    * Fixes of visual flickering of dataset selector dropdown in GPFjs
    * Fixes in handling of internal state in GPFjs

* 2024.6.6
    * Update for GRR info pages for genomic scores, gene scores, gene models
      and reference genome
    * Demo annotators for external tools using batch mode annotation
    * Demo annotators for external tools using using GRR resources and 
      batch mode annotation
    * Fixes and optimization for genotype variants query over schema2
      parquet loader
    * Fix handling of bigWig resources in GRR
    * Fix home page search for a gene profile
    * Fix handling of gene browser input

* 2024.6.5
    * Fix for GTF gene models parser
* 2024.6.4
    * Initial support for batch mode in annotation pipeline and
      annotate columns tool
    * Fix for gene profiles state handling in GPFjs
    * Clean up and improvements in searchable dropdowns in GPFjs
* 2024.6.3
    * Fix gene scores missing description in GRR info pages
    * DuckDb version bumpted to 1.0.0
    * Initial implementation of request caching in WDAE
    * Fix a minor issue in collapsable dropdown dataset selector
* 2024.6.2
    * Initial support for BigWig genomic resources
    * Bump GPF dependencies
    * Fix handling of phenotype browser images
    * Improved gene models statistics
    * Improved gene models and reference genome info pages in GRR
* 2024.6.1
    * Fix gene models GTF parser
    * Parallelization of phenotype data import tool
* 2024.6.0
    * Fix in hadling annotation pipeline preamble in annotation documentation
      tool
    * Imrovements in annotation documentation tool
    * Support for quering genotye variants over Schema2 parquet loader
    * Improvements in genomic scores and gene scores info packages
    * Fix in handling studies without variants in GCP Schema2 genotype
      storage
    * Fix in family tags counter
    * Collapsable dropdown dataset selector
    * Fix phenotype tool legend
    * Fix the layout of histogram description in scores descriptions

* 2024.5.3
    * Fix hanlding of genomic resources varsions in GRR home page
    * Support for multiple regression measures in phenotype databases
    * Resore basic liftover annotator
    * Fix in handling studies without variants in Impala Schema2 genotype
      storage
    * Improvments in handling annotation pipeline preamble section
    * Fix alignment of dataset names in GPF home page hierarchy
    * Fix handling of gene profiles column ordering
    * Fix families counter in dataset statistics families by pedigree page

* 2024.5.2
    * Improved styling of annotation documentation generated by annote_doc
    * Fix handling of `hidden` datasets in GPF home page hierarchy
    * Bug fix for loading datasets in GPFjs
		
* 2024.5.1
    * Annotation pipeline as genomic resource
    * Improvements in liftover annotator
    * Store column ordering in gene profiles state
    * Fix resizing of phenotype browser table
    * Source maps instrumentation of GPFjs build
		

* 2024.5.0
    * Support for preamble in annotation pipeline
    * Support for genotype studies without variants
    * Improvements in loading dataset hierarchy performance
    * Full parquet datasets variants loader
    * Store gene profiles visible columns to state
    * Fix handling of invalid URLs
