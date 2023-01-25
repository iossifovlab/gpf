"""Setup for GPF genotype storage on the GCP."""

import setuptools

setuptools.setup(
    name="gpf_gcp",
    version="3.7.dev5",
    author="Lubomir Chorbadjiev",
    author_email="lubomir.chorbadjiev@gmail.com",
    description="GPF genotype storage on the GCP",
    url="https://github.com/IossifovLab/gpf",
    packages=setuptools.find_packages(
        where=".", exclude=[
            "gcp_genotype_storage.docs", "tests.*", "*.tests.*", "*.tests", ],
    ),
    # include_package_data=True,
    package_data={
        "gcp_genotype_storage": ["py.typed"],
    },
    scripts=[
    ],
    entry_points="""
    [dae.genotype_storage.factories]
    gcp=gcp_genotype_storage.gcp_genotype_storage:GcpGenotypeStorage

    [dae.import_tools.storages]
    gcp=gcp_genotype_storage.gcp_import_storage:GcpImportStorage

    [console_scripts]

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
