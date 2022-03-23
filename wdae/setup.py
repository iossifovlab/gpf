import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="gpf_wdae",
    version="3.6.0",
    author="Lubomir Chorbadjiev",
    author_email="lubomir.chorbadjiev@gmail.com",
    description="GPF: Genotypes and Phenotypes in Families",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/IossifovLab/gpf",
    packages=setuptools.find_packages(
        where="wdae/", exclude=["docs", "*.tests.*", "tests", ]
    ),
    include_package_data=True,
    package_dir={"": "wdae"},

    package_data={"gpfjs": [
        "static/gpfjs/*", "static/gpfjs/assets/*", "static/gpfjs/empty/*"], },

    scripts=[
        "wdae/wdaemanage.py",
        "wdae/wdae_create_dev_users.sh",
        "wdae/wdae_bootstrap.sh",
    ],
    # entry_points={
    #     'console_scripts': [
    #         'scgview=scgv.qtmain:main',
    #     ]
    # },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
