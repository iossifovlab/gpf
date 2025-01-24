# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

import pytest

from dae.enrichment_tool.enrichment_cache_builder import cli
from dae.enrichment_tool.enrichment_helper import EnrichmentHelper
from dae.enrichment_tool.gene_weights_background import (
    GeneScoreEnrichmentBackground,
)
from dae.gpf_instance import GPFInstance
from dae.studies.study import GenotypeData
from dae.testing import denovo_study, setup_denovo, setup_pedigree


@pytest.fixture
def ped_1(tmp_path: pathlib.Path) -> pathlib.Path:
    return setup_pedigree(
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


@pytest.fixture
def denovo_1(tmp_path: pathlib.Path) -> pathlib.Path:
    return setup_denovo(
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
        """,
    )


@pytest.fixture
def study_1(
    tmp_path: pathlib.Path,
    t4c8_fixture: GPFInstance,
    ped_1: pathlib.Path,
    denovo_1: pathlib.Path,
) -> GenotypeData:
    return denovo_study(
        tmp_path, "study_1", ped_1, [denovo_1],
        t4c8_fixture,
        study_config_update={
            "enrichment": {
                "enabled": True,
                "selected_person_set_collections": [
                    "status",
                ],
                "selected_background_models": [
                    "coding_len_background",
                ],
                "default_background_model": "coding_len_background",
                "selected_counting_models": [
                    "enrichment_gene_counting",
                    "enrichment_events_counting",
                ],
                "counting": {
                    "enrichment_gene_counting": {
                        "id": "enrichment_gene_counting",
                        "name": "Counting affected genes",
                        "desc": "Counting affected genes",
                    },
                    "enrichment_events_counting": {
                        "id": "enrichment_events_counting",
                        "name": "Counting events",
                        "desc": "Counting events",
                    },
                },
                "default_counting_model": "enrichment_gene_counting",
                "effect_types": [
                    "LGDs", "missense", "synonymous",
                ],
            },
        })


def test_t4c8_setup(t4c8_fixture: GPFInstance) -> None:
    assert t4c8_fixture is not None
    grr = t4c8_fixture.grr
    assert grr is not None


def test_t4c8_coding_len_background(t4c8_fixture: GPFInstance) -> None:
    grr = t4c8_fixture.grr
    resource = grr.get_resource("coding_len_background")
    assert resource is not None

    background = GeneScoreEnrichmentBackground(resource)
    assert background is not None
    background.load()

    assert background.genes_weight(["t4"]) == 44
    assert background.genes_weight(["c8"]) == 45
    assert background.genes_weight(["t1"]) == 0
    assert background._total == 89

    assert background.genes_weight(["T4"]) == 44
    assert background.genes_weight(["C8"]) == 45

    assert background.genes_weight(["T4", "C8"]) == 89
    assert background.genes_weight(["T4", "C8", "T1"]) == 89


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
    t4c8_fixture: GPFInstance,
) -> None:
    enriichment_helper = EnrichmentHelper(t4c8_fixture.grr)
    assert enriichment_helper is not None

    results = enriichment_helper.calc_enrichment_test(
        study_1,
        "status",
        ["t4"],
        effect_groups=["LGDs", "missense", "synonymous"],
        background_id="coding_len_background",
        counter_id="enrichment_events_counting",
    )

    assert results is not None
    affected = results["affected"]

    res = affected["LGDs"]
    assert res.all.events == 2
    assert res.all.overlapped == 0
    assert res.all.expected == pytest.approx(0.988, 0.001)

    res = affected["missense"]
    assert res.all.events == 2
    assert res.all.overlapped == 2
    assert res.all.expected == pytest.approx(0.988, 0.001)

    res = affected["synonymous"]
    assert res.all.events == 3
    assert res.all.overlapped == 2
    assert res.all.expected == pytest.approx(1.483, 0.001)


def test_study_1_enrichment_with_caching(
    study_1: GenotypeData,
    t4c8_fixture: GPFInstance,
) -> None:

    enriichment_helper = EnrichmentHelper(t4c8_fixture.grr)
    assert enriichment_helper is not None

    enriichment_helper.build_enrichment_event_counts_cache(
        study_1, "status",
    )

    results = enriichment_helper.calc_enrichment_test(
        study_1,
        "status",
        ["t4"],
        effect_groups=["LGDs", "missense", "synonymous"],
        background_id="coding_len_background",
        counter_id="enrichment_events_counting",
    )

    assert results is not None
    affected = results["affected"]

    res = affected["LGDs"]
    assert res.all.events == 2
    assert res.all.overlapped == 0
    assert res.all.expected == pytest.approx(0.988, 0.001)

    res = affected["missense"]
    assert res.all.events == 2
    assert res.all.overlapped == 2
    assert res.all.expected == pytest.approx(0.988, 0.001)

    res = affected["synonymous"]
    assert res.all.events == 3
    assert res.all.overlapped == 2
    assert res.all.expected == pytest.approx(1.483, 0.001)


def test_build_study_1_enrichment_cache(
    study_1: GenotypeData,
    t4c8_fixture: GPFInstance,
) -> None:
    assert not (
        pathlib.Path(study_1.config_dir) / "enrichment_cache.json").exists()

    cli(["--studies", "study_1"], t4c8_fixture)

    assert (
        pathlib.Path(study_1.config_dir) / "enrichment_cache.json").exists()

    enriichment_helper = EnrichmentHelper(t4c8_fixture.grr)
    assert enriichment_helper is not None
    cache = enriichment_helper._load_enrichment_event_counts_cache(study_1)

    assert cache is not None
    assert len(cache) == 2

    events = cache["enrichment_events_counting"]["affected"]["LGDs"]
    assert events["all"] == 2
    assert events["rec"] == 1
    assert events["female"] == 2

    events = cache["enrichment_events_counting"]["affected"]["missense"]
    assert events["all"] == 2
    assert events["rec"] == 1
    assert events["female"] == 2

    events = cache["enrichment_events_counting"]["affected"]["synonymous"]
    assert events["all"] == 3
    assert events["rec"] == 1
    assert events["female"] == 3

    events = cache["enrichment_gene_counting"]["affected"]["LGDs"]
    assert events["all"] == 1
    assert events["rec"] == 1
    assert events["female"] == 1

    events = cache["enrichment_gene_counting"]["affected"]["missense"]
    assert events["all"] == 1
    assert events["rec"] == 1
    assert events["female"] == 1

    events = cache["enrichment_gene_counting"]["affected"]["synonymous"]
    assert events["all"] == 2
    assert events["rec"] == 1
    assert events["female"] == 2
