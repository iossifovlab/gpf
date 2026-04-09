"""Setup for GPF Genomic Annotation INfrastructure (GAIN)."""

import pathlib

import setuptools
import versioneer

long_description = pathlib.Path("README.md").read_text(encoding="utf8") \
    if pathlib.Path("README.md").exists() else ""


setuptools.setup(
    name="gain-core",
    version=versioneer.get_version(),  # type: ignore
    cmdclass=versioneer.get_cmdclass(),  # type: ignore
    author="Lubomir Chorbadjiev",
    author_email="lubomir.chorbadjiev@gmail.com",
    description="GAIn: Genomic Annotation Infrastructure",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/IossifovLab/gpf",
    packages=setuptools.find_packages(
        where=".", exclude=[
            "tests.*", "tests", "gain.docs", "gain.tests", "*.tests.*",
            "*.tests",
        ],
    ),
    package_data={
        "gain": ["py.typed"],
        "gain.annotation": ["templates/annotate_doc_pipeline_template.jinja"],
        "gain.dask": ["named_cluster.yaml"],
        "gain.genomic_resources": ["repo_info_scripts.html"],
    },
    scripts=[
    ],
    entry_points="""
    [gain.genomic_resources.plugins]
    default_grr=gain.genomic_resources.genomic_context:DefaultRepositoryContextProvider
    cli_genomic_context=gain.genomic_resources.genomic_context_cli:CLIGenomicContextProvider
    cli_annotation_context=gain.annotation.annotation_genomic_context_cli:CLIAnnotationContextProvider

    [gain.genomic_resources.implementations]
    position_score=gain.genomic_resources.implementations.genomic_scores_impl:GenomicScoreImplementation
    np_score=gain.genomic_resources.implementations.genomic_scores_impl:GenomicScoreImplementation
    allele_score=gain.genomic_resources.implementations.genomic_scores_impl:GenomicScoreImplementation
    liftover_chain=gain.genomic_resources.implementations.liftover_chain_impl:LiftoverChainImplementation
    genome=gain.genomic_resources.implementations.reference_genome_impl:ReferenceGenomeImplementation
    gene_models=gain.genomic_resources.implementations.gene_models_impl:GeneModelsImpl
    cnv_collection=gain.genomic_resources.implementations.genomic_scores_impl:CnvCollectionImplementation
    annotation_pipeline=gain.genomic_resources.implementations.annotation_pipeline_impl:AnnotationPipelineImplementation
    gene_score=gain.gene_scores.implementations.gene_scores_impl:build_gene_score_implementation_from_resource
    gene_set_collection=gain.gene_sets.implementations.gene_sets_impl:build_gene_set_collection_implementation_from_resource
    gene_set=gain.gene_sets.implementations.gene_sets_impl:build_gene_set_collection_implementation_from_resource

    [gain.annotation.annotators]
    allele_score=gain.annotation.score_annotator:build_allele_score_annotator
    allele_score_annotator=gain.annotation.score_annotator:build_allele_score_annotator
    np_score=gain.annotation.score_annotator:build_np_score_annotator
    np_score_annotator=gain.annotation.score_annotator:build_np_score_annotator
    position_score=gain.annotation.score_annotator:build_position_score_annotator
    position_score_annotator=gain.annotation.score_annotator:build_position_score_annotator
    effect_annotator=gain.annotation.effect_annotator:build_effect_annotator
    gene_set_annotator=gain.annotation.gene_set_annotator:build_gene_set_annotator
    liftover_annotator=gain.annotation.liftover_annotator:build_liftover_annotator
    basic_liftover_annotator=gain.annotation.liftover_annotator:build_liftover_annotator
    bcf_liftover_annotator=gain.annotation.liftover_annotator:build_liftover_annotator
    normalize_allele_annotator=gain.annotation.normalize_allele_annotator:build_normalize_allele_annotator
    gene_score_annotator=gain.annotation.gene_score_annotator:build_gene_score_annotator
    simple_effect_annotator=gain.annotation.simple_effect_annotator:build_simple_effect_annotator
    cnv_collection=gain.annotation.cnv_collection_annotator:build_cnv_collection_annotator
    cnv_collection_annotator=gain.annotation.cnv_collection_annotator:build_cnv_collection_annotator
    chrom_mapping=gain.annotation.chrom_mapping_annotator:build_chrom_mapping_annotator
    debug_annotator=gain.annotation.debug_annotator:build_annotator

    [console_scripts]
    demo_graphs_cli=gain.task_graph.demo_graphs_cli:main

    grr_manage=gain.genomic_resources.cli:cli_manage
    grr_browse=gain.genomic_resources.cli:cli_browse

    annotate_variant_effects=gain.effect_annotation.cli:cli_columns
    annotate_variant_effects_vcf=gain.effect_annotation.cli:cli_vcf

    annotate_columns=gain.annotation.annotate_columns:cli
    annotate_vcf=gain.annotation.annotate_vcf:cli
    annotate_doc=gain.annotation.annotate_doc:cli
    draw_score_histograms=gain.genomic_resources.draw_score_histograms:main
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
