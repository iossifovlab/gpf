"""Setup for GPF data access environment (DAE)."""

import pathlib

import setuptools
import versioneer

long_description = pathlib.Path("README.md").read_text(encoding="utf8")


setuptools.setup(
    name="gpf_dae",
    version=versioneer.get_version(),  # type: ignore
    cmdclass=versioneer.get_cmdclass(),  # type: ignore
    author="Lubomir Chorbadjiev",
    author_email="lubomir.chorbadjiev@gmail.com",
    description="GPF: Genotypes and Phenotypes in Families",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/IossifovLab/gpf",
    packages=setuptools.find_packages(
        where=".", exclude=[
            "tests.*", "tests", "dae.docs", "dae.tests", "*.tests.*",
            "*.tests",
        ],
    ),
    package_data={
        "dae": ["py.typed"],
        "dae.dask": ["named_cluster.yaml"],
        "dae.annotation": ["templates/annotate_doc_pipeline_template.jinja"],
    },
    scripts=[
    ],
    entry_points="""
    [dae.genomic_resources.plugins]
    default_grr=dae.genomic_resources.genomic_context:DefaultRepositoryContextProvider
    cli_genomic_context=dae.genomic_resources.genomic_context_cli:CLIGenomicContextProvider
    cli_annotation_context=dae.annotation.annotation_genomic_context_cli:CLIAnnotationContextProvider
    gpf_instance_context=dae.gpf_instance_plugin.gpf_instance_context_plugin:GPFInstanceContextProvider

    [dae.genomic_resources.implementations]
    gene_set_collection=dae.gene_sets.implementations.gene_sets_impl:build_gene_set_collection_implementation_from_resource
    gene_set=dae.gene_sets.implementations.gene_sets_impl:build_gene_set_collection_implementation_from_resource
    gene_score=dae.gene_scores.implementations.gene_scores_impl:build_gene_score_implementation_from_resource
    position_score=dae.genomic_resources.implementations.genomic_scores_impl:GenomicScoreImplementation
    np_score=dae.genomic_resources.implementations.genomic_scores_impl:GenomicScoreImplementation
    allele_score=dae.genomic_resources.implementations.genomic_scores_impl:GenomicScoreImplementation
    liftover_chain=dae.genomic_resources.implementations.liftover_chain_impl:LiftoverChainImplementation
    genome=dae.genomic_resources.implementations.reference_genome_impl:ReferenceGenomeImplementation
    vcf_info=dae.genomic_resources.vcf_info_score:build_vcf_info_from_resource
    gene_models=dae.genomic_resources.implementations.gene_models_impl:GeneModelsImpl
    cnv_collection=dae.genomic_resources.implementations.genomic_scores_impl:CnvCollectionImplementation
    gene_weights_enrichment_background=dae.enrichment_tool.resource_implementations.enrichment_resource_impl:build_gene_weights_enrichment_background
    samocha_enrichment_background=dae.enrichment_tool.resource_implementations.enrichment_resource_impl:build_samocha_enrichment_background
    annotation_pipeline=dae.genomic_resources.implementations.annotation_pipeline_impl:AnnotationPipelineImplementation

    [dae.annotation.annotators]
    allele_score=dae.annotation.score_annotator:build_allele_score_annotator
    np_score=dae.annotation.score_annotator:build_np_score_annotator
    position_score=dae.annotation.score_annotator:build_position_score_annotator
    effect_annotator=dae.annotation.effect_annotator:build_effect_annotator
    gene_set_annotator=dae.annotation.gene_set_annotator:build_gene_set_annotator
    liftover_annotator=dae.annotation.liftover_annotator:build_liftover_annotator
    basic_liftover_annotator=dae.annotation.liftover_annotator:build_liftover_annotator
    bcf_liftover_annotator=dae.annotation.liftover_annotator:build_liftover_annotator
    normalize_allele_annotator=dae.annotation.normalize_allele_annotator:build_normalize_allele_annotator
    gene_score_annotator=dae.annotation.gene_score_annotator:build_gene_score_annotator
    simple_effect_annotator=dae.annotation.simple_effect_annotator:build_simple_effect_annotator
    cnv_collection=dae.annotation.cnv_collection_annotator:build_cnv_collection_annotator
    chrom_mapping=dae.annotation.chrom_mapping_annotator:build_chrom_mapping_annotator
    debug_annotator=dae.annotation.debug_annotator:build_annotator

    [dae.genotype_storage.factories]
    inmemory=dae.inmemory_storage.inmemory_genotype_storage:InmemoryGenotypeStorage
    duckdb_legacy=dae.duckdb_storage.duckdb_legacy_genotype_storage:DuckDbLegacyStorage
    duckdb=dae.duckdb_storage.duckdb_genotype_storage:duckdb_storage_factory
    duckdb_parquet=dae.duckdb_storage.duckdb_genotype_storage:duckdb_parquet_storage_factory
    duckdb_s3_parquet=dae.duckdb_storage.duckdb_genotype_storage:duckdb_s3_parquet_storage_factory
    duckdb_s3=dae.duckdb_storage.duckdb_genotype_storage:duckdb_s3_storage_factory
    parquet=dae.parquet_storage.storage:ParquetGenotypeStorage

    [dae.import_tools.storages]
    schema2=dae.schema2_storage.schema2_import_storage:Schema2ImportStorage
    inmemory=dae.inmemory_storage.inmemory_import_storage:InmemoryImportStorage
    duckdb_legacy=dae.duckdb_storage.duckdb_import_storage:DuckDbLegacyImportStorage
    duckdb=dae.duckdb_storage.duckdb_import_storage:DuckDbImportStorage
    duckdb_parquet=dae.duckdb_storage.duckdb_import_storage:DuckDbParquetImportStorage
    duckdb_s3_parquet=dae.duckdb_storage.duckdb_import_storage:DuckDbS3ParquetImportStorage
    duckdb_s3=dae.duckdb_storage.duckdb_import_storage:DuckDbS3ImportStorage
    parquet=dae.parquet_storage.storage:ParquetImportStorage

    [console_scripts]
    demo_graphs_cli=dae.task_graph.demo_graphs_cli:main

    grr_manage=dae.genomic_resources.cli:cli_manage
    grr_browse=dae.genomic_resources.cli:cli_browse
    grr_cache_repo=dae.tools.grr_cache_repo:cli_cache_repo

    annotate_variant_effects=dae.effect_annotation.cli:cli_columns
    annotate_variant_effects_vcf=dae.effect_annotation.cli:cli_vcf

    annotate_columns=dae.annotation.annotate_columns:cli
    annotate_vcf=dae.annotation.annotate_vcf:cli
    annotate_doc=dae.annotation.annotate_doc:cli
    annotate_schema2_parquet=dae.parquet.schema2.annotate_schema2_parquet:cli
    reannotate_instance=dae.annotation.reannotate_instance:cli
    pheno_import=dae.pheno.pheno_import:main
    import_tools_pheno=dae.pheno.import_tools:main
    import_phenotypes=dae.pheno.import_tools:main
    build_pheno_browser=dae.pheno.build_pheno_browser:main
    update_pheno_descriptions=dae.pheno.update_pheno_descriptions:main


    agp_exporter=dae.gene_profile.exporter:cli_export

    ped2ped=dae.tools.ped2ped:main
    draw_pedigree=dae.tools.draw_pedigree:main
    draw_score_histograms=dae.genomic_resources.draw_score_histograms:main

    generate_vcf_score_histogram.py=dae.tools.generate_vcf_score_histogram:main
    gpf_validation_runner=dae.tools.gpf_validation_runner:main
    gpf_instance_adjustments=dae.gpf_instance.adjustments.gpf_instance_adjustments:cli
    gpf_convert_study_config=dae.tools.gpf_convert_study_config:main
    denovo_liftover=dae.tools.denovo_liftover:main
    dae_liftover=dae.tools.liftover_tools:dae_liftover_main
    cnv_liftover=dae.tools.liftover_tools:cnv_liftover_main
    vcf_liftover=dae.tools.vcf_liftover:main

    import_tools=dae.import_tools.cli:main
    import_genotypes=dae.import_tools.cli:main
    generate_gene_profile=dae.gene_profile.generate_gene_profile:main
    convert_gene_profile_to_duckdb=dae.gene_profile.convert_gene_profile_to_duckdb:main
    generate_common_report=dae.tools.generate_common_report:main
    generate_denovo_gene_sets=dae.tools.generate_denovo_gene_sets:main

    build_coding_length_enrichment_background=dae.enrichment_tool.build_coding_length_enrichment_background:cli
    build_ur_synonymous_enrichment_background=dae.enrichment_tool.build_ur_synonymous_enrichment_background:cli
    enrichment_cache_builder=dae.enrichment_tool.enrichment_cache_builder:cli
    to_gpf_gene_models_format=dae.tools.to_gpf_gene_models_format:main
    simple_study_import=dae.tools.simple_study_import:main

    denovo2vcf=dae.tools.denovo2vcf:main
    dae2vcf=dae.tools.dae2vcf:main
    vcf2tsv=dae.tools.vcf2tsv:main
    """,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    zip_safe=False,
)
