"""Setup for GPF remote extension."""

import setuptools
import versioneer

setuptools.setup(
    name="gpf_federation",
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
        "federation": ["py.typed"],
    },
    scripts=[],
    entry_points="""
    [wdae.gpf_instance.extensions]
    remote_extension=federation.remote_extension:GPFRemoteExtension
    [federation.tools]
    pheno_tool=federation.remote_pheno_tool_adapter:RemotePhenoToolAdapter
    enrichment_helper=federation.remote_enrichment_tool:RemoteEnrichmentHelper
    enrichment_builder=federation.remote_enrichment_tool:RemoteEnrichmentBuilder
    pheno_browser_helper=federation.remote_pheno_browser_helper:RemotePhenoBrowserHelper
    common_reports_helper=federation.remote_common_reports_helper:RemoteCommonReportsHelper
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
