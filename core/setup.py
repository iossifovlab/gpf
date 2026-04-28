"""Setup for GPF data access environment (DAE)."""

import pathlib

import setuptools
import versioneer

long_description = pathlib.Path("README.md").read_text(encoding="utf8")


setuptools.setup(
    name="gpf-core",
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
            "tests.*", "tests", "gpf.docs", "gpf.tests", "*.tests.*",
            "*.tests",
        ],
    ),
    package_data={
        "gpf": ["py.typed"],
    },
    scripts=[
    ],
    entry_points="""
    [gpf.genotype_storage.factories]
    inmemory=gpf.inmemory_storage.inmemory_genotype_storage:InmemoryGenotypeStorage
    duckdb_legacy=gpf.duckdb_storage.duckdb_legacy_genotype_storage:DuckDbLegacyStorage
    duckdb=gpf.duckdb_storage.duckdb_genotype_storage:duckdb_storage_factory
    duckdb_parquet=gpf.duckdb_storage.duckdb_genotype_storage:duckdb_parquet_storage_factory
    duckdb_s3_parquet=gpf.duckdb_storage.duckdb_genotype_storage:duckdb_s3_parquet_storage_factory
    duckdb_s3=gpf.duckdb_storage.duckdb_genotype_storage:duckdb_s3_storage_factory
    parquet=gpf.parquet_storage.storage:ParquetGenotypeStorage

    [gpf.import_tools.storages]
    schema2=gpf.schema2_storage.schema2_import_storage:Schema2ImportStorage
    inmemory=gpf.inmemory_storage.inmemory_import_storage:InmemoryImportStorage
    duckdb_legacy=gpf.duckdb_storage.duckdb_import_storage:DuckDbLegacyImportStorage
    duckdb=gpf.duckdb_storage.duckdb_import_storage:DuckDbImportStorage
    duckdb_parquet=gpf.duckdb_storage.duckdb_import_storage:DuckDbParquetImportStorage
    duckdb_s3_parquet=gpf.duckdb_storage.duckdb_import_storage:DuckDbS3ParquetImportStorage
    duckdb_s3=gpf.duckdb_storage.duckdb_import_storage:DuckDbS3ImportStorage
    parquet=gpf.parquet_storage.storage:ParquetImportStorage

    [console_scripts]
    grr_cache_repo=gpf.tools.grr_cache_repo:cli_cache_repo

    annotate_schema2_parquet=gpf.parquet.schema2.annotate_schema2_parquet:cli
    pheno_import=gpf.pheno.pheno_import:main
    import_tools_pheno=gpf.pheno.import_tools:main
    import_phenotypes=gpf.pheno.import_tools:main
    build_pheno_browser=gpf.pheno.build_pheno_browser:main
    update_pheno_descriptions=gpf.pheno.update_pheno_descriptions:main


    agp_exporter=gpf.gene_profile.exporter:cli_export

    ped2ped=gpf.tools.ped2ped:main
    draw_pedigree=gpf.tools.draw_pedigree:main
    generate_vcf_score_histogram.py=gpf.tools.generate_vcf_score_histogram:main
    gpf_validation_runner=gpf.tools.gpf_validation_runner:main
    gpf_instance_adjustments=gpf.gpf_instance.adjustments.gpf_instance_adjustments:cli
    gpf_convert_study_config=gpf.tools.gpf_convert_study_config:main
    denovo_liftover=gpf.tools.liftover_tools:denovo_liftover_main
    dae_liftover=gpf.tools.liftover_tools:dae_liftover_main
    cnv_liftover=gpf.tools.liftover_tools:cnv_liftover_main
    vcf_liftover=gpf.tools.liftover_tools:vcf_liftover_main

    import_tools=gpf.import_tools.cli:main
    import_genotypes=gpf.import_tools.cli:main
    generate_gene_profile=gpf.gene_profile.generate_gene_profile:main
    convert_gene_profile_to_duckdb=gpf.gene_profile.convert_gene_profile_to_duckdb:main
    generate_common_report=gpf.tools.generate_common_report:main
    generate_denovo_gene_sets=gpf.tools.generate_denovo_gene_sets:main

    build_coding_length_enrichment_background=gpf.enrichment_tool.build_coding_length_enrichment_background:cli
    build_ur_synonymous_enrichment_background=gpf.enrichment_tool.build_ur_synonymous_enrichment_background:cli
    enrichment_cache_builder=gpf.enrichment_tool.enrichment_cache_builder:cli
    to_gpf_gene_models_format=gpf.tools.to_gpf_gene_models_format:main
    simple_study_import=gpf.tools.simple_study_import:main

    denovo2vcf=gpf.tools.denovo2vcf:main
    dae2vcf=gpf.tools.dae2vcf:main
    vcf2tsv=gpf.tools.vcf2tsv:main
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
