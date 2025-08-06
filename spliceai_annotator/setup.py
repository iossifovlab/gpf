"""Setup for GPF schema2 genotype storage on Apache Impala v4.x."""

import setuptools
import versioneer

setuptools.setup(
    name="gpf_spliceai_annotator",
    version=versioneer.get_version(),  # type: ignore
    cmdclass=versioneer.get_cmdclass(),  # type: ignore
    author="Lubomir Chorbadjiev",
    author_email="lubomir.chorbadjiev@gmail.com",
    description="GPF SpliceAI annotator plugin",
    url="https://github.com/IossifovLab/gpf",
    packages=setuptools.find_packages(
        where=".", exclude=[
            "spliceai_annotator.docs", "tests.*", "*.tests.*", "*.tests"],
    ),
    package_data={
        "spliceai_annotator": [
            "py.typed",
            "models/spliceai1.h5",
            "models/spliceai2.h5",
            "models/spliceai3.h5",
            "models/spliceai4.h5",
            "models/spliceai5.h5",
        ],
    },
    scripts=[
    ],
    entry_points="""
    [dae.annotation.annotators]
    spliceai_annotator=spliceai_annotator:build_spliceai_annotator

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
