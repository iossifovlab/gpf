"""Setup for GPF data access environment (DAE)."""

import setuptools

with open("README.md", "r", encoding="utf8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gpf_dae",
    version="3.7.dev5",
    author="Lubomir Chorbadjiev",
    author_email="lubomir.chorbadjiev@gmail.com",
    description="GPF: Genotypes and Phenotypes in Families",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/IossifovLab/gpf",
    packages=setuptools.find_packages(
        where=".", exclude=[
            "tests.*", "tests", "dae.docs", "dae.tests", "*.tests.*",
            "*.tests"
        ],
    ),
    package_data={
        "dae": ["py.typed"],
        "dae.dask": ["named_cluster.yaml"],
    },
    scripts=[
        "dae/tools/impala_parquet_loader.py",
        "dae/tools/impala_tables_loader.py",
        "dae/tools/impala_tables_stats.py",
        "dae/tools/impala_tables_summary_variants.py",
        "dae/tools/hdfs_parquet_loader.py",
        "dae/tools/generate_common_report.py",
        "dae/tools/generate_denovo_gene_sets.py",
        "dae/tools/pheno2dae.py",
        "dae/tools/pheno2browser.py",
        "dae/tools/simple_pheno_import.py",
        "dae/tools/simple_study_import.py",
        "dae/tools/run_gpf_impala.sh",
        "dae/tools/simple_family2pedigree.py",
        "dae/tools/ped2parquet.py",
        "dae/tools/ped2ped.py",
        "dae/tools/draw_pedigree.py",
        "dae/tools/impala_batch_import.py",
        "dae/tools/remote_instance_mirror.py",
        "dae/tools/genotype_data_tool.py",
        "dae/tools/vcfinfo_extractor.py",
        "dae/tools/generate_autism_gene_profile.py",
    ],
    entry_points="""
    [dae.genomic_resources.plugins]
    default_grr=dae.genomic_resources.genomic_context:DefaultRepositoryContextProvider.register
    gpf_instance=dae.gpf_instance_plugin.gpf_instance_context_plugin:init_gpf_instance_genomic_context_plugin

    [dae.genomic_resources.implementations]
    gene_set=dae.gene.gene_sets_db:build_gene_set_collection_from_resource
    gene_score=dae.gene.gene_scores:build_gene_score_collection_from_resource
    position_score=dae.genomic_resources.genomic_scores:build_position_score_from_resource
    np_score=dae.genomic_resources.genomic_scores:build_np_score_from_resource
    allele_score=dae.genomic_resources.genomic_scores:build_allele_score_from_resource
    liftover_chain=dae.genomic_resources.liftover_resource:build_liftover_chain_from_resource
    genome=dae.genomic_resources.reference_genome:build_reference_genome_from_resource
    vcf_info=dae.genomic_resources.vcf_info_score:build_vcf_info_from_resource
    gene_models=dae.genomic_resources.gene_models:build_gene_models_from_resource

    [dae.annotation.annotators]
    allele_score=dae.annotation.score_annotator:build_allele_score_annotator
    np_score=dae.annotation.score_annotator:build_np_score_annotator
    position_score=dae.annotation.score_annotator:build_position_score_annotator
    effect_annotator=dae.annotation.effect_annotator:build_effect_annotator
    liftover_annotator=dae.annotation.liftover_annotator:build_liftover_annotator
    normalize_allele_annotator=dae.annotation.normalize_allele_annotator:build_normalize_allele_annotator
    gene_score_annotator=dae.annotation.gene_score_annotator:build_gene_score_annotator
    simple_effect_annotator=dae.annotation.simple_effect_annotator:build_simple_effect_annotator

    [dae.genotype_storage.factories]
    impala=dae.impala_storage.schema1.impala_genotype_storage:ImpalaGenotypeStorage
    impala2=dae.impala_storage.schema2.impala2_genotype_storage:Impala2GenotypeStorage
    inmemory=dae.inmemory_storage.inmemory_genotype_storage:InmemoryGenotypeStorage
    duckdb=dae.duckdb_storage.duckdb_genotype_storage:DuckDbGenotypeStorage

    [dae.import_tools.storages]
    impala=dae.impala_storage.schema1.impala_schema1:ImpalaSchema1ImportStorage
    impala2=dae.impala_storage.schema2.impala2_import_storage:Impala2ImportStorage
    schema2=dae.schema2_storage.schema2_import_storage:Schema2ImportStorage
    inmemory=dae.inmemory_storage.inmemory_import_storage:InmemoryImportStorage
    duckdb=dae.duckdb_storage.duckdb_import_storage:DuckDbImportStorage

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


    agp_exporter=dae.autism_gene_profile.exporter:cli_export

    ped2ped=dae.tools.ped2ped:main
    draw_pedigree=dae.tools.draw_pedigree:main

    dae2parquet.py=dae.tools.dae2parquet:main
    vcf2parquet.py=dae.tools.vcf2parquet:main
    vcf2schema2.py=dae.backends.schema2.vcf2schema2:main
    denovo2parquet.py=dae.tools.denovo2parquet:main
    cnv2parquet.py=dae.tools.cnv2parquet:main
    generate_vcf_score_histogram.py=dae.tools.generate_vcf_score_histogram:main
    gpf_validation_runner=dae.tools.gpf_validation_runner:main
    gpf_instance_adjustments=dae.tools.gpf_instance_adjustments:cli
    denovo_liftover=dae.tools.denovo_liftover:main
    dae_liftover=dae.tools.dae_liftover:main
    stats_liftover=dae.tools.stats_liftover:main

    import_tools=dae.import_tools.cli:main
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
