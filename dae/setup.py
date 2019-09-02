
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gpf_dae",
    version="3.0.0a1",
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
        'dae/annotation/annotation_pipeline.py',
        'dae/tools/generate_histogram.py',
    ],

    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
