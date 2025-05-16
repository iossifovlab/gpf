Release Notes
=============

* 2025.5.5
    * Reorganization of GPF federation plugin.
    * Fix support for CNV in variants query grammar.
    * Fix regions filter text area.

* 2025.5.4
    * GPF federation regorganization.
    * Support for phenotype instruments and measures update.
    * Fix VEP annotator plugin for newer version of VEP.
    * Bump version of Lark parser library to 1.2.2.
    * Update GRR gene set collection info pages.
    * Clean up dae and wdae testing infrastructure.
    * Clean up phenotype browser measure domains.
    * Support for instruments and measures tooltips in phenotype browser.

* 2025.5.3
    * Fix handling of phenotype measures error state in GPFjs.
    * Update GPF federation plugin.
    * Reorganization of GPF instance adjustements tool.

* 2025.5.2
    * Fix rebuilding of phenotype browser cache in wgpf tool.
    * Clean up common reports logging.
    * Adjust default working directory for genotype import tool.
    * Allow editing of home page description when permissions are disabled.
    * Fix Y-axys ticks in histograms.
    * Fix validation of gene symbols in genes component.
    * Support for automatic table preview in genotype browser.

* 2025.5.1
    * Fix support for queries by role.
    * Allow missing work directory in phenotype data import project.
    * Support for instrument description in phenotype data import project.
    * Remove study phenotype from default study configuration.
    * Fixes in gene symbols validation.
    * Fixes in histograms y-axis labels.

* 2025.5.0
    * Fix support for default configuration of denovo gene sets.
    * Clean up CLI tool for generation of denovo gene sets.
    * Invoke the CLI tool for generation of denovo gene sets from the
      wgpf tool.
    * Fixes in GPF federation plugin.
    * Fixes in gene symbols validation.

* 2025.4.10
    * Fix grr_cache_repo tool to use embedded annotation configuration.
    * Improve performance of re-annotation tool checks for reannotation.


* 2025.4.9
    * Fix CNV variants frequency filtering.
    * Support for default commont report configuration for phenotype data.
    * Support for default study configuration with download columns from
      annotation.
    * Fix default configuration of phenotype measure filters.
    * Clean up phenotype browser cache build tool invocation in wgpf tool.
    * Fix default configuration of enrichment tool.
    * Add link to registration info into login page.
    * Fix keybindings in phenotype measrues filters.
    * Fix phenotype measures description popup dialog.

* 2025.4.8
    * Fix default CNV study configuration generated at import in DuckDb
      genotype storage.
    * Auto-scroll to table preview in the genotype browser when results
      are loaded.
    * Fix tool selection bug when navigating from Gene Profiles to
      Gene Browser.
    * Enhance separation of internal and external links in Gene Profiles single
      view.
    * Reset zygosity filters when switching between datasets.

* 2025.4.7
    * Fix phenotype browser cache regeneration in wgpf tools.

* 2025.4.6
    * Fix heuristics for Y log scale in histograms.
    * Fix roles queries in legacy genotype storages.
    * Support for filters by zygosity in sexes in DuckDb genotype storage.
    * Change default columns in DenovoLoader format.
    * Add timeout argument to the GPF REST client query variants method.
    * Fix de Novo icon in dataset dropdown and hierarchy.
    * Fix loading pheno measure filters from UI state.


* 2025.4.5
    * Enable pheno measure filters by default when a genotype study has
      phenotype data.
    * Genotype data groups should deduce has_denovo and has_transmitted flags
      from children.
    * Enable pheno tool by default when a genotype study has phenotype data and
      de novo variants.
    * Support for filters by zygosity in roles in DuckDb genotype storage.
    * Adjust default study configuration to make GSG fluent.
    * Fix pheno measure filters user interface.
    * Reorganize genotype browser filters ordering.
    * Support for filters by zygosity in Present in Child and Present in
      Parent in genotype browser.
    * Fix histograms bars with zero height.
    * Support pheno measure description in pheno measure filters.


* 2025.4.4
    * Support for queries by zygosity in roles in DuckDb genotype storage.
    * Support for inlining annotation in GPF instance configuration.
    * Adjust import genotypes CLI tool default working directory.
    * Adjust import phenotypes CLI tool default working directory.
    * Support for automatic re-annotation in wgpf CLI tool.
    * Fix pedigree loading in phenotype studies.
    * Fix phenotype studies pedigree downloads.
    * Update default genotype data configuration.

* 2025.4.3
    * Bug fix in handling of permissions on phenotype data.

* 2025.4.2
    * Fix command line tool for generation of dataset statistics.
    * Fix phenotype data families data to load family tags.
    * Fix queryies by family tags in Apache Impala Schema1 genotype storage.
    * Support for queries by zygosity in statuses in DuckdDb genotype storage.
    * Fix in liftover annotator.

* 2025.4.1
    * Consistent CLI interface and implementation for all annotation.
    * Support for common reports in phenotype data groups.
    * Reorganization of datasets hierarchy user interface.
    * Switch to using DuckDb genotype storage for default internal storage.
    * Reorganization of GPF rest client tokens.
    * Genotype storage support for query by family tags.
    * Fix support for INDELs in SpliceAI annotator plugin.
    * Support for more attributes and aggregation of attributes in SpliceAI
      annotator plugin.


* 2025.4.0
    * Fix values domain ordering in phenotype data import.
    * Fix GRR histogram labels on X-axis in case of X log scale.
    * Initial implementation of SpliceAI annotator plugion.
    * Support for validation in gene symbols edit box in genotype browser.
    * Fix visual bug in Safari browser in gene profiles single view.


* 2025.3.7
    * Fix present in parent default values in phenotype tool.
    * Bump dependencies versions.
    * Clean up testing of GRR HTTP protocol support.

* 2025.3.6
    * Fix present in parent default values.
    * Support for getting roles from phenotype data groups.
    * Fix VEP annotator plugin attributes types.

* 2025.3.5
    * Fix gene profiles search for gene symbols.
    * Clean up VEP annotator plugin documentation support.
    * Fix VEP annotator plugin open method.
    * Support for configutation of histograms in phenotype data import.
    * Support heuristics for log scale Y axis in histograms.
    * Fix sorting of gene consequences in VEP annotator plugin.
    * Fix handling of genome prefix in regions filter block.

* 2025.3.4
    * Clean up handling of genome prefix.


* 2025.3.3
    * Fixes in VEP annotator plugin.
    * Updates in CNV collection annotator.
    * Fixes in handling of .gz files in annotate columns tool.

* 2025.3.2
    * Extend support for genomic context in all annotation tools.
    * Fixes in GPF REST client library.
    * Support for phenotype measures filtering by role.
    * Support for batch annotation in import tools.
    * Fix GTF parsing and serialization.
    * Clean up enrichment tool configuration.
    * Fix handling of categorical histograms labels.
    * Fix transmitted rare variants filter.
    * Improvements in categorical histograms user interface.
    * Update phenotype family and person filters to include roles. 

* 2025.3.1
    * Fix permissions for any_user group with annonymous user.
    * Fix in handling of empty lines in VEP annotator plugin.
    * Fix GRR histograms modals.
    * Fix VEP annotator plugin handling of unknown attributes.
    * Clean up GRR manage tool support for single region tasks.
    * Add VEP annotator plugion tool for cache download.
    * Fix VEP annotator plugin writing to context.
    * Fix handling of whitespaces in dataset description.
    * Improvement in handling of labels in categorical histograms.
    * Fix categorical histograms handling of order in categorical histograms.


* 2025.3.0
    * Fix datasets hierarchy with hidden datasets.
    * Fix ordering of studies in genotype data groups.
    * Support for label rotation in categorical histograms.
    * Expand gene set collection GRR info page.
    * Fix support for phenotype person and family filters in genotype browser.
    * 

* 2025.2.2
    * Fix phenotype group hierarchy construction.
    * Fix access rights for datasets hierarchy requests.
    * Fix genomic scores header width.
    * Update person filter styles.

* 2025.2.1
    * Support VEP annotator plugin using VEP Docker container.
    * Support for phenotype mearures filtering using value and histogram types.
    * Support for description in phenotype studies.

* 2025.2.0
    * Update gene profiles configuration.
    * Introduction of phenotype storage and phenotype storage registry
    * Support phenotype data into datasets hierarchy
    * Update and fix CNV collection statistics
    * Improvements in phenotype data import and phenotype browser cache
    * Initial support for VCF serialization of full variants iterator from variant loaders
    * Support for phenotype data common reports
    * Support for full pedigree information in phenotype data import
    * Adjust wgpf tool to support phenotype data stides and groups
    * Support for categorical histograms label rotation
    * Fix for phenotype data group merge instruments function
    * Support for categorical genomic scores in the UI
    * Support for multiple views for categorical histograms UI
    * Support for label rotation in categorical histograms UI


* 2025.1.4
    * Fix deserialization of variant attributes.

* 2025.1.3
    * Clean up phenotype browser cache build tool.
    * Fix support for categorical genomic scores queries.
    * Deprecation of `import_tools` and introduction of `genotypes_import`.
    * Deprecation of `import_tools_pheno` and introduction of `phenotypes_import`.
    * Fix support for categorical histograms for genomic scores.

* 2025.1.2
    * Fix wgpf tool.

* 2025.1.1
    * Fix queries by present in child and present in parent.

* 2025.1.0
    * Update the model for saving queries.
    * Gene Browser performance optimization.
    * Added support for downloading Phenotype Tool report image.
    * Fix OAuth2 login request to use the proper encoding.
    * Fix OAuth2 authentication.
    * Bump version of Angular to v18.
    * Fix gene profiles single view back navigation for gene not found.
    * Support for categorical histograms in genomic scores user interface.
    * Improved unit tests coverage for GPFjs.
    * Bump versions of ECMAScript and TypeScript.
    * Extention of GPF REST client to support more REST API endpoints.
    * Switch to using DuckDb for gene profiles.
    * Fix handling of internal annotation attributes in annotate_vcf.
    * NormalizeAlleleAnnotator to support discovery of the reference genome if not specified in the annotation pipeline.
    * Change the VEP annotator plugin to use VEP in offline mode.
    * Reorganization of genomic scores resources hierarchy.
    * Reorganization of genomic scores annotators hierarchy.
    * Fix gene regions heuristics.
    * Performance improvements in VCF variant loader.
    * Support for no region split in grr_manage.
    * Implementation of GPF instance re-annotation tool.
    * Reorganization of handling of pedigrees.
    * Added index file in GRR statistics folders.
    * Fixes in family roles builder class.
    * Switch to using Pyright in GPF builds.
    * Split of the phenotype data import into separate tools.
    * Support for phenotype data import project.
    * Performance improvements in import of VCF studies in Schema2.
    * Fix calcuation of variant types in VCFAllele annotatable.
    * Clean up of GPF unit tests.
    * Reduction of memory footprint in Schema2 parquet writer.
    * Reduction of memory footprint for import tools.
    * Fix default `fill-in-mode` for VCF variant loader.
    * Refactor phenotype import measure classification.
    * Refactor tools for building phenotype browser cache.
    * Refactor phenotype data registry.
    * Bump GPF dependencies versions.
    * Switch CNV collection to use genomic scores base class.
    * Fix query variants for studies without variants.
    * Support queries by affected status in Schema2 genotype storages.
    * Support for queries by categorical genomic scores.

* 2024.12.2
    * Fix the GTF gene models parser.
    * Change the fetch_region method signature for genomic scores.
    * Fix for usage of .CONTENTS file in GRR.

* 2024.12.1
    * Fix support for GRR contents file in YAML format

* 2024.12.0
    * Restore gene scores partitions REST API
    * Clean up WDAE unit tests
    * The cnv_collection does not crash on an unknown chromosome
    * Added get_region_scores to PostionScore interface
    * Change `fetch_region` method signature for `AlleleScore`
    * Switch to using JSON format for GRR contents file
    * Reorganization of GeneSetAnnotator to support multiple gene sets
    * Fis support for downloading phenotype tool report image
    * Restore usage of gene scores partitions

* 2024.11.3
    * Fix annoate_columns to create a correct tabix index
    * Fix SimpleEffectAnnotator to produce a link to the GPF documentation
    * Adjust formatting of float numbers in annotate_columns and annotate_vcf
      tools
    * Fix gene set annotator to include attributes in the annotation schema
    * Fix gene score annotator documentation to include aggregator
    * Add support for read-only filesystem GRR
    * Add support for liftover annotator to use source and target genomes from
      liftover chain genomic resource labels
    * Annonymous users can access limited functionality of phenotype tools
    * Add support for effect annotator to use reference genome from genomic
      resource labels, annotation pipeline preamble, and genomic context
    * Fix types produced in annotation pipeline documentation
    * Fix dataset hierarchy permissions
    * Support for wildcards in annotation pipeline resource_id annotator's
      attributes
    * Fix in region splitting in annotation and reannotation tools -
      annotate_columns, annotate_vcf and annotate_schema2_parquet
    * Support for categorical histograms in gene scores user interface
    * Support for consistency checks in genomic scores fetch_region method
    * Minor optimizations in the genomic position table
    * Fix an infinite loop in the liftover annotator
    * Minor improvements in DuckDb genotype storage
    * Support for downloading phenotype tool report image
    * Fix in the error handling for family filters in the genotype browser


* 2024.11.2
    * Fix pheno import type inference issues
    * Improvments in phenotype data import unit testing
    * Improvements in enrichment REST API unit testing
    * Fix handling of `any_user` access rights in dataset hierarchy
    * Fix query cancelation in gene browser

* 2024.11.1
    * Fix pheno import type inference issues
    * Improvments in phenotype data import testing
    * Construct gene sets download ling on the frontend
    * Fix handling of frequency filters in DuckDb genotype storage
    * Bump version DuckDb to 1.1.3
    * Implementation of full re-annotation of schema2 parquet datasets
    * Factory functions for bulding genomic resources from resource ID
    * Fix query cancelation in genotype browser
    * Improvement in handling pedigrees in dataset statistics without
      access rights

* 2024.11.0
    * Pure python implementation of type inference for phenotype measures
    * Phenotype data import refactored
    * Support for storing gene models in GTF format
    * Support for storing gene and genomic scores histograms in JSON format
    * Fix de Novo gene sets user interface
    * Fix hanling of families and persons IDs in save/share query

* 2024.10.6
    * Bug fix in handling genomic scores with chromosome remapping
    * Workaround for pysam handling of HLA contigs regions
    * Bug fix for handling dataset description without children

* 2024.10.5
    * GPF federation refactoring to create a separate conda
      package *gpf_federation*
    * Update de Novo gene sets REST API
    * Support for restricted access of GPF tools without explicit access rights
    * Improvement and fixes in Schema2 parquet datasets re-annotation
    * Bump DuckDb version to 1.1.2
    * Support for DuckDb S3 genotype storage
    * Fix missing gene profiles state in GPFjs

* 2024.10.4
    * Refactor and fixes in support of person set collection queries

* 2024.10.3
    * Remove an exception logger from phenotype measures download in
      phenotype browser

* 2024.10.2
    * Clean up user edit code from GPFjs

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
