import setuptools

import os
import sys
from pathlib import Path
from typing import Dict, List


def _expand_recursive_globs(
        root_dir: str,
        package_data: Dict[str, List[str]]) -> Dict[str, List[str]]:
    root = (Path(__file__).parent / root_dir).resolve()
    for module, patterns in package_data.items():
        new_patterns = []
        module_root = root / module
        for p in patterns:
            if "**" in p:
                pattern_prefix = p.split("**")[0]
                path_to_glob = module_root / pattern_prefix
                for f in path_to_glob.glob("**"):  # all subdirectories
                    if f.name == "__pycache__":
                        continue
                    subdir_pattern = p.replace(
                        "**", str(f.relative_to(path_to_glob))
                    )
                    new_patterns.append(subdir_pattern)
            else:
                new_patterns.append(p)
        package_data[module] = new_patterns
    return package_data


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gpf_wdae",
    version="3.7.dev5",
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
    package_data=_expand_recursive_globs("wdae", {
        "gpfjs": [
            "static/**/*",
            "templates/**/*",
        ],
        "users_api": [
            "static/**/*",
            "templates/**/*",
        ]
    }),
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
