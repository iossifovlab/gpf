# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap

import pytest
import yaml
from dae.genomic_resources.testing import (
    setup_denovo,
    setup_pedigree,
)
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.studies.study import GenotypeData
from dae.testing.alla_import import alla_gpf
from dae.testing.import_helpers import (
    denovo_study,
    study_update,
)

from studies.study_wrapper import WDAEStudy


@pytest.fixture
def gpf_fixture(tmp_path_factory: pytest.TempPathFactory) -> GPFInstance:
    root_path = tmp_path_factory.mktemp(
        "genotype_browser_columns_config")
    return alla_gpf(root_path)


@pytest.fixture
def trio_study(
    tmp_path_factory: pytest.TempPathFactory,
    gpf_fixture: GPFInstance,
) -> GenotypeData:
    root_path = tmp_path_factory.mktemp(
        "genotype_browser_columns_config")
    ped_path = setup_pedigree(
        root_path / "trio_data" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     1   2      prb
        f1       s1       d1     m1     1   1      sib
        """)
    vcf_path = setup_denovo(
        root_path / "trio_data" / "in.tsv",
        """
          chrom  pos ref  alt  person_id
          foo    7   A    G    p1,s1
        """,
    )

    return denovo_study(
        root_path,
        "trio", ped_path, [vcf_path],
        gpf_instance=gpf_fixture,
        study_config_update={
            "id": "trio",
        })


def test_genotype_browser_preview_columns_default(
    trio_study: GenotypeData,
) -> None:
    config = trio_study.config.genotype_browser

    assert config.preview_columns == [
        "family", "variant", "genotype", "effect", "frequency",
    ]


def test_genotype_browser_download_columns_default(
    trio_study: GenotypeData,
) -> None:

    config = trio_study.config.genotype_browser

    assert config.download_columns == [
        "family", "variant", "variant_extra",
        "family_person_ids", "family_structure", "best", "family_genotype",
        "carriers", "inheritance", "phenotypes",
        "par_called", "allele_freq",
        "effect", "geneeffect", "effectdetails",
    ]


def test_genotype_browser_preview_columns_ext(
    trio_study: GenotypeData,
    gpf_fixture: GPFInstance,
) -> None:
    study = study_update(
        gpf_fixture, trio_study, yaml.safe_load(textwrap.dedent("""
        genotype_browser:
            columns:
                genotype:
                    aaa:
                        name: AAA
                        source: aaa
            preview_columns_ext:
                - aaa
        """)),
    )
    config = study.config.genotype_browser
    assert config.preview_columns_ext == [
        "aaa",
    ]


def test_genotype_browser_download_columns_ext(
    trio_study: GenotypeData,
    gpf_fixture: GPFInstance,
) -> None:

    study = study_update(
        gpf_fixture, trio_study, yaml.safe_load(textwrap.dedent("""
        genotype_browser:
            columns:
                genotype:
                    aaa:
                        name: AAA
                        source: aaa
            download_columns_ext:
                - aaa
        """)),
    )
    config = study.config.genotype_browser
    assert config.download_columns_ext == [
        "aaa",
    ]


def test_study_wrapper_preview_columns_ext(
    trio_study: GenotypeData,
    gpf_fixture: GPFInstance,
) -> None:

    study = study_update(
        gpf_fixture, trio_study, yaml.safe_load(textwrap.dedent("""
        genotype_browser:
            columns:
                genotype:
                    aaa:
                        name: AAA
                        source: aaa
            preview_columns_ext:
                - aaa
        """)),
    )
    wrapper = WDAEStudy(gpf_fixture.genotype_storages, study, None)
    assert wrapper.preview_columns == [
        "family", "variant", "genotype", "effect", "frequency", "aaa",
    ]


def test_study_wrapper_download_columns_ext(
    trio_study: GenotypeData,
    gpf_fixture: GPFInstance,
) -> None:

    study = study_update(
        gpf_fixture, trio_study, yaml.safe_load(textwrap.dedent("""
        genotype_browser:
            columns:
                genotype:
                    aaa:
                        name: AAA
                        source: aaa
            download_columns_ext:
                - aaa
        """)),
    )
    wrapper = WDAEStudy(gpf_fixture.genotype_storages, study, None)
    assert wrapper.download_columns == [
        "family", "variant", "variant_extra",
        "family_person_ids", "family_structure", "best", "family_genotype",
        "carriers", "inheritance", "phenotypes",
        "par_called", "allele_freq",
        "effect", "geneeffect", "effectdetails",
        "aaa",
    ]
