# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap
import pytest

from dae.testing import setup_pedigree, setup_denovo, denovo_study
from dae.testing.foobar_import import foobar_gpf


@pytest.fixture
def trios2_study(tmp_path_factory):
    root_path = tmp_path_factory.mktemp(
        "denovo_gene_sets_tios")
    gpf_instance = foobar_gpf(root_path)
    ped_path = setup_pedigree(
        root_path / "trios2_data" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     1   2      prb
        f2       m2       0      0      2   1      mom
        f2       d2       0      0      1   1      dad
        f2       p2       d2     m2     1   2      prb
        """)
    vcf_path = setup_denovo(
        root_path / "trios2_data" / "in.tsv",
        """
          familyId  location  variant    bestState
          f1        foo:10    sub(A->G)  2||2||1||1/0||0||1||0
          f1        foo:11    sub(T->A)  2||2||1||2/0||0||1||0
          f1        bar:10    sub(G->A)  2||2||2||1/0||0||0||1
          f2        bar:11    sub(G->A)  2||2||1/0||0||1
          f2        bar:12    sub(G->A)  2||2||1/0||0||1
        """
    )

    study = denovo_study(
        root_path,
        "trios2", ped_path, [vcf_path],
        gpf_instance,
        study_config_update=textwrap.dedent("""
        id: trios2
        denovo_gene_sets:
          enabled: True
        """))
    return study


def test_trios2_study_simple(trios2_study):
    config = trios2_study.config

    assert config is not None
    assert config.denovo_gene_sets is not None

    assert config.denovo_gene_sets.enabled


def test_default_dgs_config_selected_person_sets(trios2_study):
    config = trios2_study.config

    assert config.denovo_gene_sets.selected_person_set_collections == \
        ["status"]


def test_default_dgs_config_standard_criterias_effect_types(trios2_study):
    config = trios2_study.config

    assert "effect_types" in config.denovo_gene_sets.standard_criterias

    effect_types = config.denovo_gene_sets.standard_criterias.effect_types
    assert effect_types == {
        "segments": {
            "LGDs": "LGDs",
            "Missense": "missense",
            "Synonymous": "synonymous",
        }
    }


def test_default_dgs_config_standard_criterias_sexes(trios2_study):
    config = trios2_study.config

    assert "sexes" in config.denovo_gene_sets.standard_criterias

    sexes = config.denovo_gene_sets.standard_criterias.sexes
    assert sexes == {
        "segments": {
            "Female": "F",
            "Male": "M",
            "Unspecified": "U",
        }
    }


def test_default_dgs_config_recurrency_criteria(trios2_study):
    config = trios2_study.config

    assert "segments" in config.denovo_gene_sets.recurrency_criteria

    segments = config.denovo_gene_sets.recurrency_criteria.segments
    assert segments["Single"] == {
        "start": 1,
        "end": 2,
    }

    assert segments["Triple"] == {
        "start": 3,
        "end": -1,
    }

    assert segments["Recurrent"] == {
        "start": 2,
        "end": -1,
    }
