# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

import pytest

from dae.studies.study import GenotypeData
from dae.gpf_instance import GPFInstance
from dae.enrichment_tool.gene_weights_background import \
    GeneWeightsEnrichmentBackground
from dae.enrichment_tool.enrichment_helper import EnrichmentHelper

from dae.testing import setup_pedigree, setup_denovo, denovo_study


@pytest.fixture
def ped_1(tmp_path: pathlib.Path) -> pathlib.Path:
    ped_path = setup_pedigree(
        tmp_path / "input" / "ped_1" / "in.ped",
        """
familyId personId dadId momId sex status role
f1.1     mom1     0     0     2   1      mom
f1.1     dad1     0     0     1   1      dad
f1.1     ch1      dad1  mom1  2   2      prb
f1.3     mom3     0     0     2   1      mom
f1.3     dad3     0     0     1   1      dad
f1.3     ch3      dad3  mom3  2   2      prb
        """)
    return ped_path


@pytest.fixture
def denovo_1(tmp_path: pathlib.Path) -> pathlib.Path:
    denovo_path = setup_denovo(
        tmp_path / "input" / "denovo_1" / "denovo.tsv",
        """
familyId  location  variant    bestState
f1.1      chr1:52   sub(C->A)  2||2||1/0||0||1
f1.3      chr1:52   sub(C->T)  2||2||1/0||0||1
f1.1      chr1:53   sub(A->C)  2||2||1/0||0||1
f1.3      chr1:54   sub(T->C)  2||2||1/0||0||1
f1.1      chr1:57   sub(A->G)  2||2||1/0||0||1
f1.3      chr1:114  sub(C->T)  2||2||1/0||0||1
f1.1      chr1:195  sub(C->T)  2||2||1/0||0||1
f1.3      chr1:145  sub(C->T)  2||2||1/0||0||1
        """
    )
    return denovo_path


@pytest.fixture
def study_1(
    tmp_path: pathlib.Path,
    t4c8_fixture: GPFInstance,
    ped_1: pathlib.Path,
    denovo_1: pathlib.Path,
) -> GenotypeData:
    result = denovo_study(
        tmp_path, "study_1", ped_1, [denovo_1],
        t4c8_fixture,
        study_config_update={
            "enrichment": {
                "enabled": True,
                "selected_person_set_collections": [
                    "status"
                ],
                "selected_background_models": [
                    "coding_len_background",
                ],
                "default_background_model": "coding_len_background",
                "selected_counting_models": [
                    "enrichment_gene_counting",
                    "enrichment_events_counting"
                ],
                "counting": {
                    "enrichment_gene_counting": {
                        "id": "enrichment_gene_counting",
                        "name": "Counting affected genes",
                        "desc": "Counting affected genes"
                    },
                    "enrichment_events_counting": {
                        "id": "enrichment_events_counting",
                        "name": "Counting events",
                        "desc": "Counting events"
                    }
                },
                "default_counting_model": "enrichment_gene_counting",
                "effect_types": [
                    "LGDs", "missense", "synonymous"
                ]
            }
        })
    return result


def test_t4c8_setup(t4c8_fixture: GPFInstance) -> None:
    assert t4c8_fixture is not None
    grr = t4c8_fixture.grr
    assert grr is not None


def test_t4c8_coding_len_background(t4c8_fixture: GPFInstance) -> None:
    grr = t4c8_fixture.grr
    resource = grr.get_resource("coding_len_background")
    assert resource is not None

    background = GeneWeightsEnrichmentBackground(resource)
    assert background is not None
    background.load()

    assert background.genes_weight(["t4"]) == 41
    assert background.genes_weight(["c8"]) == 43
    assert background.genes_weight(["t1"]) == 0
    assert background._total == 84

    assert background.genes_weight(["T4"]) == 41
    assert background.genes_weight(["C8"]) == 43

    assert background.genes_weight(["T4", "C8"]) == 84
    assert background.genes_weight(["T4", "C8", "T1"]) == 84


def test_study_1(study_1: GenotypeData) -> None:
    assert study_1 is not None
    vs = list(study_1.query_variants())
    assert len(vs) == 8

    vs = list(study_1.query_variants(effect_types=["missense"]))
    assert len(vs) == 3

    vs = list(study_1.query_variants(effect_types=["synonymous"]))
    assert len(vs) == 3

    vs = list(study_1.query_variants(effect_types=["LGDs"]))
    assert len(vs) == 2


def test_study_1_enrichment(
    study_1: GenotypeData,
    t4c8_fixture: GPFInstance
) -> None:
    enriichment_helper = EnrichmentHelper(t4c8_fixture.grr)
    assert enriichment_helper is not None

    results = enriichment_helper.calc_enrichment_test(
        study_1,
        "status",
        ["T4"],
        effect_groups=["LGDs", "missense", "synonymous"],
        background_id="coding_len_background",
        counter_id="enrichment_events_counting",
    )

    assert results is not None
    affected = results["affected"]

    res = affected["LGDs"]
    assert res.all.events == 2
    assert res.all.overlapped == 0
    assert res.all.expected == pytest.approx(0.976, 0.001)

    res = affected["missense"]
    assert res.all.events == 2
    assert res.all.overlapped == 2
    assert res.all.expected == pytest.approx(0.976, 0.001)

    res = affected["synonymous"]
    assert res.all.events == 3
    assert res.all.overlapped == 2
    assert res.all.expected == pytest.approx(1.464, 0.001)
