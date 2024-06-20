"""Setup for GPF Dummy Annotator."""

import setuptools
import versioneer

setuptools.setup(
    name="gpf_external_demo_annotator",
    version=versioneer.get_version(),  # type: ignore
    cmdclass=versioneer.get_cmdclass(),  # type: ignore
    author="Lubomir Chorbadjiev",
    author_email="lubomir.chorbadjiev@gmail.com",
    description="GPF External Demo Annotator",
    url="https://github.com/IossifovLab/gpf",
    packages=setuptools.find_packages(
        where=".", exclude=[
            "tests.*", "*.tests.*", "*.tests"],
    ),
    package_data={
        "demo_annotator": ["py.typed"],
    },
    entry_points="""
    [console_scripts]
    annotate_length=demo_annotator.annotate_length:annotate_length_cli
    annotate_genes=demo_annotator.annotate_genes:annotate_genes_cli
    annotate_reference_genome=demo_annotator.annotate_reference_genome:annotate_genome_cli
    [dae.annotation.annotators]
    external_demo_annotator=demo_annotator.adapter:build_demo_external_annotator_adapter
    external_demo_stream_annotator=demo_annotator.adapter:build_demo_external_annotator_stream_adapter
    external_demo_gene_annotator=demo_annotator.gene_models_adapter:build_demo_external_gene_annotator_adapter
    external_demo_genome_annotator=demo_annotator.reference_genome_adapter:build_demo_external_genome_annotator_adapter
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
