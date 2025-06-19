# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from box import Box
from dae.gene_profile.statistic import GPStatistic
from dae.genomic_resources.gene_models.gene_models import Exon, TranscriptModel
from django.test.client import Client
from gpf_instance.gpf_instance import WGPFInstance
from pytest_mock import MockerFixture

ROUTE_PREFIX = "/api/v3/gene_profiles"


def test_configuration(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,
    mocker: MockerFixture,
) -> None:
    mock_conf = {
        "defaultDataset": "ALL_genotypes",
        "geneLinks": [{
            "name": "MockLink",
            "url": "{gpf_prefix}/{gene}/{genome}/",
        }],
        "confDir": "/data",
        "datasets": [{
            "id": "MockDataset",
        }],
    }
    mocker.patch.object(
        t4c8_wgpf_instance, "get_wdae_gp_configuration",
        return_value=mock_conf,
    )

    response = admin_client.get(f"{ROUTE_PREFIX}/single-view/configuration")

    assert response.status_code == 200
    assert response.data == mock_conf  # type: ignore
    print(response.data)  # type: ignore


def test_get_statistic(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,
    mocker: MockerFixture,
) -> None:
    mock_gp_statistic = GPStatistic(
        "CHD8",
        ["gene_set_1", "gene_set_2"],
        {
            "category_1": {
                "genomic_score_1": {
                    "score_1": {
                        "value_1": 1,
                        "value_2": 2,
                    },
                },
            },
        },
        {
            "study_1": {
                "autism": {
                    "lgds": {
                        "count": 1.0,
                        "rate": 1000.0,
                    },
                    "denovo_missense": {
                        "count": 1.0,
                        "rate": 1000.0,
                    },
                },
                "unaffected": {
                    "lgds": {
                        "count": 0.0,
                        "rate": 0.0,
                    },
                    "denovo_missense": {
                        "count": 2.0,
                        "rate": 2000.0,
                    },
                },
            },
        },
    )
    mocker.patch.object(
        t4c8_wgpf_instance, "get_gp_statistic",
        return_value=mock_gp_statistic,
    )

    response = admin_client.get(f"{ROUTE_PREFIX}/single-view/gene/CHD8")
    assert response.data["geneSymbol"] == "CHD8"  # type: ignore
    assert response.data["geneSets"] == ["gene_set_1", "gene_set_2"]  # type: ignore
    assert response.data["geneScores"] == [{  # type: ignore
        "id": "category_1",
        "scores": [{
            "id": "genomic_score_1",
            "score_1": {
                "value_1": 1,
                "value_2": 2,
            },
        }],
    }]
    assert response.data["studies"] == [{  # type: ignore
        "id": "study_1",
        "personSets": [
            {
                "id": "autism",
                "effectTypes": [
                    {
                        "id": "lgds",
                        "value": {
                            "count": 1.0,
                            "rate": 1000.0,
                        },
                    },
                    {
                        "id": "denovo_missense",
                        "value": {
                            "count": 1.0,
                            "rate": 1000.0,
                        },
                    },
                ],
            },
            {
                "id": "unaffected",
                "effectTypes": [
                    {
                        "id": "lgds",
                        "value": {
                            "count": 0.0,
                            "rate": 0.0,
                        },
                    },
                    {
                        "id": "denovo_missense",
                        "value": {
                            "count": 2.0,
                            "rate": 2000.0,
                        },
                    },
                ],
            },
        ],
    }]

    assert response.status_code == 200
    print(response.data)  # type: ignore


def test_get_links(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,
    monkeypatch: pytest.MonkeyPatch,
    mocker: MockerFixture,
) -> None:
    """Test gene profile links."""
    mocker.patch.object(
        t4c8_wgpf_instance, "get_gp_statistic",
        return_value=GPStatistic("CHD8", [], {}, {}),
    )

    mocker.patch.object(
        t4c8_wgpf_instance, "get_genotype_data_config",
        return_value=Box({"genome": "mock_genome"}),
    )

    mocker.patch.object(
        t4c8_wgpf_instance, "get_transcript_models",
        return_value=(
            "CHD8", [
                TranscriptModel("CHD8", "", "", "mock_chr", "", (0, 0), (0, 0),
                    [Exon(1, 2, 0), Exon(3, 4, 0)]),
                TranscriptModel("CHD8", "", "", "mock_chr", "", (0, 0), (0, 0),
                    [Exon(5, 6, 0), Exon(7, 8, 0)]),
                TranscriptModel("CHD8", "", "", "mock_chr", "", (0, 0), (0, 0),
                    [Exon(9, 10, 0), Exon(11, 12, 0)]),
            ],
        ),
    )

    mocker.patch.object(
        t4c8_wgpf_instance, "get_wdae_gp_configuration",
        return_value={
            "defaultDataset": "ALL_genotypes",
            "geneLinks": [{
                "name": "MockLink",
                "url": (
                    "{gpf_prefix}/{gene}/{genome}/"
                    "{chromosome_prefix}/{chromosome}/"
                    "{gene_start_position}/{gene_stop_position}"
                ),
            }],
        },
    )

    monkeypatch.setenv("WDAE_PREFIX", "hg38")

    response = admin_client.get(f"{ROUTE_PREFIX}/single-view/gene/chd8")
    assert response.status_code == 200
    assert response.data["geneLinks"] == [  # type: ignore
        {
            "name": "MockLink",
            "url": "hg38/CHD8/mock_genome/chr/mock_chr/1/12",
        },
    ]

    print(response.data["geneLinks"])  # type: ignore


def test_get_statistics(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,
    mocker: MockerFixture,
) -> None:
    mocker.patch.object(
        t4c8_wgpf_instance, "query_gp_statistics",
        return_value=[
            GPStatistic("CHD8", [], {}, {}).to_json(),
            GPStatistic("DIABLO", [], {}, {}).to_json(),
            GPStatistic("FARP1", [], {}, {}).to_json(),
        ],
    )
    response = admin_client.get(f"{ROUTE_PREFIX}/table/rows")
    assert response.data[0]["geneSymbol"] == "CHD8"  # type: ignore
    assert response.data[1]["geneSymbol"] == "DIABLO"  # type: ignore
    assert response.data[2]["geneSymbol"] == "FARP1"  # type: ignore

    print(response.data)  # type: ignore


def test_get_gene_symbols(
    admin_client: Client,
    t4c8_wgpf_instance: WGPFInstance,
    mocker: MockerFixture,
) -> None:
    mocker.patch.object(
        t4c8_wgpf_instance, "list_gp_gene_symbols",
        return_value=["CHD8", "DIABLO", "FARP1"],
    )
    response = admin_client.get(f"{ROUTE_PREFIX}/table/gene_symbols")
    assert response.status_code == 200
    assert response.data == ["CHD8", "DIABLO", "FARP1"]  # type: ignore
