from pathlib import Path

import setuptools
import versioneer


def _collect_typing(
    root_dir: str,
) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    root = (Path(__file__).parent / root_dir).resolve()
    for fpath in root.glob("*/py.typed"):
        module = str(fpath.relative_to(root).parent)
        if module not in result:
            result[module] = []
        result[module].append("py.typed")
    return result


def _expand_recursive_globs(
    root_dir: str,
    package_data: dict[str, list[str]],
) -> dict[str, list[str]]:
    result: dict[str, list[str]] = _collect_typing(root_dir)
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
                        "**", str(fpath.relative_to(path_to_glob)),
                    )
                    new_patterns.append(subdir_pattern)
            else:
                new_patterns.append(pat)
        if module not in result:
            result[module] = new_patterns
        else:
            result[module].extend(new_patterns)
    return result


long_description = Path("README.md").read_text(encoding="utf8")

setuptools.setup(
    name="gpf_wdae",
    version=versioneer.get_version(),  # type: ignore
    cmdclass=versioneer.get_cmdclass(),  # type: ignore
    author="Lubomir Chorbadjiev",
    author_email="lubomir.chorbadjiev@gmail.com",
    description="GPF: Genotypes and Phenotypes in Families",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/IossifovLab/gpf",
    packages=setuptools.find_namespace_packages(
        where="wdae/", exclude=[
            "*.tests", "*.tests.*", "docs"],
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
        ],
    }),
    entry_points={
        "console_scripts": [
            "wgpf=wdae.wgpf:cli",
            "wdaemanage=wdae.wdaemanage:main",
            "wdaemanage.py=wdae.wdaemanage:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)
