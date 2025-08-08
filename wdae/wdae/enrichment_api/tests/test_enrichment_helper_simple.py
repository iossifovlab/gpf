# pylint: disable=W0621,C0114,C0116,W0212,W0613
from collections.abc import Callable

from dae.enrichment_tool.enrichment_utils import (
    get_enrichment_config,
)
from dae.enrichment_tool.gene_weights_background import (
    GeneScoreEnrichmentBackground,
)
from dae.enrichment_tool.samocha_background import SamochaEnrichmentBackground
from dae.gpf_instance import GPFInstance
from dae.studies.study import GenotypeData
from studies.study_wrapper import WDAEStudy

from enrichment_api.enrichment_helper import EnrichmentHelper


def test_gpf_fixture(t4c8_fixture: GPFInstance) -> None:
    grr = t4c8_fixture.grr
    res = grr.get_resource("enrichment/samocha_testing")
    assert res.get_type() == "samocha_enrichment_background"


def test_get_study_background(
    f1_trio: GenotypeData,
    t4c8_fixture: GPFInstance,
) -> None:
    assert t4c8_fixture.grr.repo_id == "enrichment_testing_repo"

    helper = EnrichmentHelper(
        t4c8_fixture.grr,
        WDAEStudy(t4c8_fixture.genotype_storages, f1_trio, None),
    )

    assert isinstance(
        helper.create_background(
            "enrichment/coding_len_testing",
        ),
        GeneScoreEnrichmentBackground,
    )

    assert isinstance(
        helper.create_background(
            "enrichment/samocha_testing",
        ),
        SamochaEnrichmentBackground,
    )


def test_get_study_enrichment_config(
    f1_trio: GenotypeData,
) -> None:
    assert get_enrichment_config(f1_trio) is not None


def test_get_selected_counting_models(
    create_test_study: Callable[[dict], GenotypeData],
    t4c8_fixture: GPFInstance,
) -> None:
    study_config = {
        "enrichment": {
            "enabled": True,
            "selected_background_models": ["enrichment/samocha_testing"],
            "selected_counting_models": ["enrichment_gene_counting"],
            "counting": {
                "enrichment_events_counting": {
                    "id": "enrichment_events_counting",
                    "name": "Counting events",
                    "desc": "Counting events",
                },
                "enrichment_gene_counting": {
                    "id": "enrichment_gene_counting",
                    "name": "Counting affected genes",
                    "desc": "Counting affected genes",
                },
            },
        },
    }

    helper = EnrichmentHelper(
        t4c8_fixture.grr,
        WDAEStudy(
            t4c8_fixture.genotype_storages,
            create_test_study(study_config),
            None,
        ),
    )
    assert helper.get_selected_counting_models() == [
        "enrichment_gene_counting"]


def test_get_selected_counting_models_default(
    create_test_study: Callable[[dict], GenotypeData],
    t4c8_fixture: GPFInstance,
) -> None:
    study_config = {
        "enrichment": {
            "enabled": True,
            "selected_background_models": ["enrichment/samocha_testing"],
        },
    }
    helper = EnrichmentHelper(
        t4c8_fixture.grr,
        WDAEStudy(
            t4c8_fixture.genotype_storages,
            create_test_study(study_config),
            None,
        ),
    )
    assert helper.get_selected_counting_models() == [
        "enrichment_events_counting", "enrichment_gene_counting"]


def test_get_selected_counting_models_default_with_counting(
    create_test_study: Callable[[dict], GenotypeData],
    t4c8_fixture: GPFInstance,
) -> None:
    study_config = {
        "enrichment": {
            "enabled": True,
            "selected_background_models": ["enrichment/samocha_testing"],
            "counting": {
                "enrichment_events_counting": {
                    "id": "enrichment_events_counting",
                    "name": "Counting events",
                    "desc": "Counting events",
                },
            },
        },
    }
    helper = EnrichmentHelper(
        t4c8_fixture.grr,
        WDAEStudy(
            t4c8_fixture.genotype_storages,
            create_test_study(study_config),
            None,
        ),
    )
    assert helper.get_selected_counting_models() == [
        "enrichment_events_counting",
        "enrichment_gene_counting",
    ]


def test_get_default_background_model(
    create_test_study: Callable[[dict], GenotypeData],
    t4c8_fixture: GPFInstance,
) -> None:
    study_config = {
        "enrichment": {
            "enabled": True,
            "selected_background_models": [
                "enrichment/samocha_testing",
                "enrichment/samocha_background",
            ],
            "default_background_model": "enrichment/samocha_background",
        },
    }

    helper = EnrichmentHelper(
        t4c8_fixture.grr,
        WDAEStudy(
            t4c8_fixture.genotype_storages,
            create_test_study(study_config),
            None,
        ),
    )
    assert helper.get_default_background_model() == \
        "enrichment/samocha_background"


def test_get_default_background_model_default(
    create_test_study: Callable[[dict], GenotypeData],
    t4c8_fixture: GPFInstance,
) -> None:
    study_config = {
        "enrichment": {
            "enabled": True,
            "selected_background_models": [
                "hg38/enrichment/coding_length_ref_gene_v20170601",
                "enrichment/samocha_background",
                "hg38/enrichment/ur_synonymous_SFARI_SSC_WGS_2",
            ],
        },
    }

    helper = EnrichmentHelper(
        t4c8_fixture.grr,
        WDAEStudy(
            t4c8_fixture.genotype_storages,
            create_test_study(study_config),
            None,
        ),
    )
    assert helper.get_default_background_model() == \
        "hg38/enrichment/coding_length_ref_gene_v20170601"


def test_get_selected_person_set_collections(
    create_test_study: Callable[[dict], GenotypeData],
    t4c8_fixture: GPFInstance,
) -> None:
    study_config = {
        "enrichment": {
            "enabled": True,
            "selected_background_models": ["enrichment/samocha_testing"],
            "selected_person_set_collections": ["role"],
        },
        "person_set_collections": {
            "phenotype": {"id": "phenotype", "name": "Phenotype"},
            "status": {"id": "status", "name": "Affected Status"},
            "role": {"id": "role", "name": "Role"},
        },
    }

    helper = EnrichmentHelper(
        t4c8_fixture.grr,
        WDAEStudy(
            t4c8_fixture.genotype_storages,
            create_test_study(study_config),
            None,
        ),
    )
    assert helper.get_selected_person_set_collections() == "role"


def test_get_selected_person_set_collections_default(
    create_test_study: Callable[[dict], GenotypeData],
    t4c8_fixture: GPFInstance,
) -> None:
    study_config = {
        "enrichment": {
            "enabled": True,
            "selected_background_models": ["enrichment/samocha_testing"],
        },
        "person_set_collections": {
            "phenotype": {"id": "phenotype",
            "name": "Phenotype",
            "sources": [{"from": "pedigree", "source": "status"}],
            "domain": [
                {"id": "autism",
                "name": "autism",
                "values": ["affected"],
                "color": "#ff2121"},
                {"id": "unaffected",
                "name": "unaffected",
                "values": ["unaffected"],
                "color": "#ffffff"},
            ],
            "default": {"id": "unspecified", "name": "unspecified", "color": "#aaaaaa"}},  # noqa: E501
            "status": {"id": "status",
            "name": "Affected Status",
            "sources": [{"from": "pedigree", "source": "status"}],
            "domain": [
                {"id": "affected",
                "name": "affected",
                "values": ["affected"],
                "color": "#ff2121"},
                {"id": "unaffected",
                "name": "unaffected",
                "values": ["unaffected"],
                "color": "#ffffff"},
            ],
            "default": {"id": "unspecified", "name": "unspecified", "color": "#aaaaaa"}},  # noqa: E501
            "role": {"id": "role",
            "name": "Role",
            "sources": [{"from": "pedigree", "source": "role"}],
            "domain": [
                {"id": "prb",
                "name": "Proband",
                "values": ["prb"],
                "color": "#ff2121"},
                {"id": "sib",
                 "name": "Sibling",
                 "values": ["sib"], "color": "#ffffff"},
            ],
            "default": {"id": "unspecified", "name": "unspecified", "color": "#aaaaaa"}},  # noqa: E501
            "selected_person_set_collections": ["role", "status", "phenotype"],
    }}

    helper = EnrichmentHelper(
        t4c8_fixture.grr,
        WDAEStudy(
            t4c8_fixture.genotype_storages,
            create_test_study(study_config),
            None,
        ),
    )
    assert helper.get_selected_person_set_collections() == "role"
