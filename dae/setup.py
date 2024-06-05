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
        "dae/tools/generate_denovo_gene_sets.py",
        "dae/tools/pheno2browser.py",
        "dae/tools/simple_study_import.py",
        "dae/tools/simple_family2pedigree.py",
        "dae/tools/ped2ped.py",
        "dae/tools/draw_pedigree.py",
        "dae/tools/vcfinfo_extractor.py",
        "dae/tools/to_gpf_gene_models_format.py",
    ],
    entry_points="""
    [dae.genomic_resources.plugins]
    default_grr=dae.genomic_resources.genomic_context:DefaultRepositoryContextProvider.register
    gpf_instance=dae.gpf_instance_plugin.gpf_instance_context_plugin:init_gpf_instance_genomic_context_plugin

    [dae.genomic_resources.implementations]
    gene_set=dae.gene_sets.gene_sets_db:build_gene_set_collection_from_resource
    gene_score=dae.gene_scores.implementations.gene_scores_impl:build_gene_score_implementation_from_resource
    position_score=dae.genomic_resources.implementations.genomic_scores_impl:GenomicScoreImplementation
    np_score=dae.genomic_resources.implementations.genomic_scores_impl:GenomicScoreImplementation
    allele_score=dae.genomic_resources.implementations.genomic_scores_impl:GenomicScoreImplementation
    liftover_chain=dae.genomic_resources.implementations.liftover_chain_impl:LiftoverChainImplementation
    genome=dae.genomic_resources.implementations.reference_genome_impl:ReferenceGenomeImplementation
    vcf_info=dae.genomic_resources.vcf_info_score:build_vcf_info_from_resource
    gene_models=dae.genomic_resources.implementations.gene_models_impl:GeneModelsImpl
    cnv_collection=dae.genomic_resources.cnv_collection:CnvCollectionImplementation
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
    debug_annotator=dae.annotation.debug_annotator:build_annotator

    [dae.genotype_storage.factories]
    inmemory=dae.inmemory_storage.inmemory_genotype_storage:InmemoryGenotypeStorage
    duckdb=dae.duckdb_storage.duckdb_genotype_storage:DuckDbGenotypeStorage
    duckdb2=dae.duckdb_storage.duckdb_genotype_storage:DuckDbGenotypeStorage
    parquet=dae.parquet_variants:ParquetGenotypeStorage

    [dae.import_tools.storages]
    schema2=dae.schema2_storage.schema2_import_storage:Schema2ImportStorage
    inmemory=dae.inmemory_storage.inmemory_import_storage:InmemoryImportStorage
    duckdb=dae.duckdb_storage.duckdb_import_storage:DuckDbImportStorage
    duckdb2=dae.duckdb_storage.duckdb_import_storage:DuckDbImportStorage
    parquet=dae.parquet_variants:ParquetImportStorage

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
    annotate_schema2_parquet=dae.annotation.annotate_schema2_parquet:cli
    pheno_import=dae.tools.pheno_import:main


    agp_exporter=dae.gene_profile.exporter:cli_export

    ped2ped=dae.tools.ped2ped:main
    draw_pedigree=dae.tools.draw_pedigree:main

    generate_vcf_score_histogram.py=dae.tools.generate_vcf_score_histogram:main
    gpf_validation_runner=dae.tools.gpf_validation_runner:main
    gpf_instance_adjustments=dae.tools.gpf_instance_adjustments:cli
    gpf_convert_study_config=dae.tools.gpf_convert_study_config:main
    denovo_liftover=dae.tools.denovo_liftover:main
    dae_liftover=dae.tools.dae_liftover:main
    cnv_liftover=dae.tools.cnv_liftover:main
    stats_liftover=dae.tools.stats_liftover:main
    vcf_liftover=dae.tools.vcf_liftover:main

    import_tools=dae.import_tools.cli:main
    generate_gene_profile=dae.gene_profile.generate_gene_profile:main
    generate_common_report=dae.common_reports.generate_common_report:main
    generate_families_cache=dae.pedigrees.generate_families_cache:main

    build_coding_length_enrichment_background=dae.enrichment_tool.build_coding_length_enrichment_background:cli
    build_ur_synonymous_enrichment_background=dae.enrichment_tool.build_ur_synonymous_enrichment_background:cli
    enrichment_cache_builder=dae.enrichment_tool.enrichment_cache_builder:cli
    """,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    zip_safe=False,
)
