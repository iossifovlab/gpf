import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gpf_dae",
    version="3.7.dev1",
    author="Lubomir Chorbadjiev",
    author_email="lubomir.chorbadjiev@gmail.com",
    description="GPF: Genotypes and Phenotypes in Families",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/IossifovLab/gpf",
    packages=setuptools.find_packages(
        where=".", exclude=["dae.docs", "dae.tests", "*.tests.*", "*.tests", ],
    ),
    include_package_data=True,
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
        "dae/pheno/prepare/individuals2ped.py",
        "dae/tools/genotype_data_tool.py",
        "dae/tools/vcfinfo_extractor.py",
        "dae/tools/generate_autism_gene_profile.py",
    ],
    entry_points="""
    [dae.genomic_resources.plugins]
    gpf_instance=dae.gpf_instance_plugin.gpf_instance_context_plugin:init_gpf_instance_genomic_context_plugin
    [console_scripts]

    grr_manage=dae.genomic_resources.cli:cli_manage
    grr_browse=dae.genomic_resources.cli:cli_browse
    grr_cache_repo=dae.genomic_resources.cli:cli_cache_repo

    annotate_variant_effects=dae.effect_annotation.cli:cli_columns
    annotate_variant_effects_vcf=dae.effect_annotation.cli:cli_vcf

    annotate_columns=dae.annotation.annotate_columns:cli
    annotate_vcf=dae.annotation.annotate_vcf:cli

    dae2parquet.py=dae.tools.dae2parquet:main
    vcf2parquet.py=dae.tools.vcf2parquet:main
    denovo2parquet.py=dae.tools.denovo2parquet:main
    cnv2parquet.py=dae.tools.cnv2parquet:main
    generate_vcf_score_histogram.py=dae.tools.generate_vcf_score_histogram:main
    gpf_validation_runner=dae.tools.gpf_validation_runner:main
    gpf_instance_adjustments=dae.tools.gpf_instance_adjustments:cli
    denovo_liftover=dae.tools.denovo_liftover:main
    dae_liftover=dae.tools.dae_liftover:main
    stats_liftover=dae.tools.stats_liftover:main
    """,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
