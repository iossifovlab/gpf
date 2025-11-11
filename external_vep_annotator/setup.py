"""Setup for GPF VEP Annotator."""

import setuptools
import versioneer

setuptools.setup(
    name="gpf_vep_annotator",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    author="Lubomir Chorbadjiev",
    author_email="lubomir.chorbadjiev@gmail.com",
    description="GPF VEP Annotator",
    url="https://github.com/IossifovLab/gpf",
    packages=setuptools.find_packages(
        where=".", exclude=[
            "tests.*", "*.tests.*", "*.tests"],
    ),
    package_data={
        "vep_annotator": ["py.typed"],
    },
    entry_points="""
    [dae.annotation.annotators]
    vep_full_annotator=vep_annotator.vep_annotator:build_vep_cache_annotator
    vep_effect_annotator=vep_annotator.vep_annotator:build_vep_effect_annotator

    [console_scripts]
    install_vep_cache=vep_annotator.install_vep_cache:main
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
