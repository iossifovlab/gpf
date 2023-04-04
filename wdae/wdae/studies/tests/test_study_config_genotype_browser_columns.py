# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap

import yaml
import pytest

from studies.study_wrapper import StudyWrapper

from dae.testing import setup_pedigree, setup_denovo, denovo_study, alla_gpf, \
    study_update


@pytest.fixture
def gpf_fixture(tmp_path_factory):
    root_path = tmp_path_factory.mktemp(
        "genotype_browser_columns_config")
    gpf_instance = alla_gpf(root_path)
    return gpf_instance


@pytest.fixture
def trio_study(tmp_path_factory, gpf_fixture):
    root_path = tmp_path_factory.mktemp(
        "genotype_browser_columns_config")
    ped_path = setup_pedigree(
        root_path / "trio_data" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     1   2      prb
        """)
    vcf_path = setup_denovo(
        root_path / "trio_data" / "in.tsv",
        """
          familyId  location  variant    bestState
          f1        foo:7     sub(A->G)  2||2||1||1/0||0||1||0
        """
    )

    study = denovo_study(
        root_path,
        "trio", ped_path, [vcf_path],
        gpf_fixture,
        study_config_update={
            "id": "trio"
        })
    return study


def test_genotype_browser_preview_columns_default(trio_study):
    config = trio_study.config.genotype_browser

    assert config.preview_columns == [
        "family", "variant", "genotype", "effect", "gene_scores", "freq"
    ]


def test_genotype_browser_download_columns_default(trio_study):
    config = trio_study.config.genotype_browser

    assert config.download_columns == [
        "family", "study_phenotype", "variant", "variant_extra",
        "family_person_ids", "family_structure", "best", "family_genotype",
        "carriers", "inheritance", "phenotypes",
        "par_called", "allele_freq",
        "effect", "geneeffect", "effectdetails",
        "gene_scores"
    ]


def test_genotype_browser_preview_columns_ext(trio_study, gpf_fixture):
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
        """))
    )
    config = study.config.genotype_browser
    assert config.preview_columns_ext == [
        "aaa"
    ]


def test_genotype_browser_download_columns_ext(trio_study, gpf_fixture):
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
        """))
    )
    config = study.config.genotype_browser
    assert config.download_columns_ext == [
        "aaa"
    ]


def test_study_wrapper_preview_columns_ext(trio_study, gpf_fixture):
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
        """))
    )
    wrapper = StudyWrapper(study, None, None)
    assert wrapper.preview_columns == [
        "family", "variant", "genotype", "effect", "gene_scores", "freq", "aaa"
    ]


def test_study_wrapper_download_columns_ext(trio_study, gpf_fixture):
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
        """))
    )
    wrapper = StudyWrapper(study, None, None)
    assert wrapper.download_columns == [
        "family", "study_phenotype", "variant", "variant_extra",
        "family_person_ids", "family_structure", "best", "family_genotype",
        "carriers", "inheritance", "phenotypes",
        "par_called", "allele_freq",
        "effect", "geneeffect", "effectdetails",
        "gene_scores",
        "aaa"
    ]
