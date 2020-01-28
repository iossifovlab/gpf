
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gpf_dae",
    version="3.0.0dev",
    author="Lubomir Chorbadjiev",
    author_email="lubomir.chorbadjiev@gmail.com",
    description="GPF: Genotypes and Phenotypes in Families",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/IossifovLab/gpf",
    packages=setuptools.find_packages(
        where='.',
        exclude=[
            'dae.docs',
            'dae.tests',
            '*.tests.*',
            '*.tests',
        ],
    ),
    include_package_data=True,
    scripts=[
        'dae/tools/annotate_variant.py',
        'dae/tools/dae2parquet.py',
        'dae/tools/vcf2parquet.py',
        'dae/tools/denovo2parquet.py',
        'dae/tools/impala_parquet_loader.py',
        'dae/tools/generate_common_report.py',
        'dae/tools/generate_denovo_gene_sets.py',
        'dae/tools/pheno2dae.py',
        'dae/tools/pheno2browser.py',
        'dae/tools/simple_pheno_import.py',
        'dae/tools/simple_study_import.py',
        'dae/annotation/annotation_pipeline.py',
        'dae/tools/generate_histogram.py',
        'dae/tools/run_gpf_impala.sh',
        'dae/tools/simple_family2pedigree.py',
        'dae/tools/ped2parquet.py',
        'dae/tools/ped2ped.py',
        'dae/tools/draw_pedigree.py',
    ],

    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
