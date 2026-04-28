"""Setup for GPF remote extension."""

import setuptools
import versioneer

setuptools.setup(
    name="gpf_rest_client",
    version=versioneer.get_version(),  # type: ignore
    cmdclass=versioneer.get_cmdclass(),  # type: ignore
    author="Lubomir Chorbadjiev",
    author_email="lubomir.chorbadjiev@gmail.com",
    description="GPF Federation",
    url="https://github.com/IossifovLab/gpf",
    packages=setuptools.find_packages(
        where=".", exclude=[
            "tests.*", "*.tests.*", "*.tests"],
    ),
    package_data={
        "rest_client": ["py.typed"],
    },
    scripts=[],
    entry_points="""
    """,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    zip_safe=False,
)
