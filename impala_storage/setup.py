"""Setup for GPF genotype storage on the GCP."""

import setuptools

setuptools.setup(
    name="gpf_impala_storage",
    version="3.7.dev5",
    author="Lubomir Chorbadjiev",
    author_email="lubomir.chorbadjiev@gmail.com",
    description="GPF genotype storage on the GCP",
    url="https://github.com/IossifovLab/gpf",
    packages=setuptools.find_packages(
        where=".", exclude=[
            "impala.docs", "tests.*", "*.tests.*", "*.tests", ],
    ),
    # include_package_data=True,
    package_data={
        "impala": ["py.typed"],
    },
    scripts=[
        "impala_storage/tools/impala_parquet_loader.py",
        "impala_storage/tools/impala_tables_loader.py",
        "impala_storage/tools/impala_tables_stats.py",
        "impala_storage/tools/impala_tables_summary_variants.py",
        "impala_storage/tools/hdfs_parquet_loader.py",
        "impala_storage/tools/impala_batch_import.py",
        "impala_storage/tools/run_gpf_impala.sh",
    ],
    entry_points="""
    [dae.genotype_storage.factories]
    impala=impala_storage.schema1.impala_genotype_storage:ImpalaGenotypeStorage
    impala2=impala_storage.schema2.impala2_genotype_storage:Impala2GenotypeStorage

    [dae.import_tools.storages]
    impala=impala_storage.schema1.impala_schema1:ImpalaSchema1ImportStorage
    impala2=impala_storage.schema2.impala2_import_storage:Impala2ImportStorage

    [console_scripts]
    dae2parquet.py=impala_storage.tools.dae2parquet:main
    vcf2parquet.py=impala_storage.tools.vcf2parquet:main
    denovo2parquet.py=impala_storage.tools.denovo2parquet:main
    cnv2parquet.py=impala_storage.tools.cnv2parquet:main
    genotype_data_tool=impala_storage.tools.genotype_data_tool:main
    remote_instance_mirror=impala_storage.tools.remote_instance_mirror:main

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
