import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gpf_dae",
    version="3.5.8",
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
        "dae/annotation/annotation_pipeline.py",
        "dae/tools/generate_histogram.py",
        "dae/tools/generate_histogram2.py",
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
    [console_scripts]
    annotate_variants.py=dae.tools.annotate_variants:cli
    annotate_variants_vcf.py=dae.tools.annotate_variants:cli_vcf
    dae2parquet.py=dae.tools.dae2parquet:main
    vcf2parquet.py=dae.tools.vcf2parquet:main
    denovo2parquet.py=dae.tools.denovo2parquet:main
    cnv2parquet.py=dae.tools.cnv2parquet:main
    generate_vcf_score_histogram.py=dae.tools.generate_vcf_score_histogram:main
    gpf_validation_runner=dae.tools.gpf_validation_runner:main
    """,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
