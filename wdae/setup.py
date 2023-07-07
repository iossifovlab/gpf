from pathlib import Path
from typing import Dict, List

import setuptools

from dae import __version__  # type: ignore


def _expand_recursive_globs(
        root_dir: str,
        package_data: Dict[str, List[str]]) -> Dict[str, List[str]]:
    root = (Path(__file__).parent / root_dir).resolve()
    for module, patterns in package_data.items():
        new_patterns = []
        module_root = root / module
        for pat in patterns:
            if "**" in pat:
                pattern_prefix = pat.split("**")[0]
                path_to_glob = module_root / pattern_prefix
                for fpath in path_to_glob.glob("**"):  # all subdirectories
                    if fpath.name == "__pycache__":
                        continue
                    subdir_pattern = pat.replace(
                        "**", str(fpath.relative_to(path_to_glob))
                    )
                    new_patterns.append(subdir_pattern)
            else:
                new_patterns.append(pat)
        package_data[module] = new_patterns
    return package_data


with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="gpf_wdae",
    version=__version__,
    author="Lubomir Chorbadjiev",
    author_email="lubomir.chorbadjiev@gmail.com",
    description="GPF: Genotypes and Phenotypes in Families",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/IossifovLab/gpf",
    packages=setuptools.find_namespace_packages(
        where="wdae/", exclude=[
            "*.tests", "*.tests.*", "docs"]
    ),
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
    entry_points={
        "console_scripts": [
            "wgpf=wdae.wgpf:cli",
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
)
