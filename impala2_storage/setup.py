"""Setup for GPF schema2 genotype storage on Apache Impala v4.x."""

import setuptools
import versioneer

setuptools.setup(
    name="gpf_impala2_storage",
    version=versioneer.get_version(),  # type: ignore
    cmdclass=versioneer.get_cmdclass(),  # type: ignore
    author="Lubomir Chorbadjiev",
    author_email="lubomir.chorbadjiev@gmail.com",
    description="GPF Apache Impala Genotype Storage",
    url="https://github.com/IossifovLab/gpf",
    packages=setuptools.find_packages(
        where=".", exclude=[
            "impala2_storage.docs", "tests.*", "*.tests.*", "*.tests"],
    ),
    # include_package_data=True,
    package_data={
        "impala2_storage": ["py.typed"],
    },
    scripts=[
        "impala2_storage/scripts/run_gpf_impala4.sh",
    ],
    entry_points="""
    [dae.genotype_storage.factories]
    impala2=impala2_storage.schema2.impala2_genotype_storage:Impala2GenotypeStorage

    [dae.import_tools.storages]
    impala2=impala2_storage.schema2.impala2_import_storage:Impala2ImportStorage

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
