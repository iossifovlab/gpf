# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json

import pytest_mock
from django.test.client import Client
from gpf_instance.gpf_instance import WGPFInstance


def test_default_gene_models_id(
    anonymous_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = anonymous_client.get("/api/v3/genome/gene_models/default")

    assert response
    assert response.status_code == 200
    assert response.data == "t4c8_genes"  # type: ignore


def test_get_chd8_transcripts(
    anonymous_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = anonymous_client.get("/api/v3/genome/gene_models/default/t4")

    assert response
    assert response.status_code == 200
    data = response.data  # type: ignore
    assert data
    assert data["gene"] == "t4"
    transcripts = data["transcripts"]
    assert len(transcripts) == 1
    assert transcripts[0]["transcript_id"] == "tx1_1"
    assert transcripts[0]["strand"] == "+"
    assert transcripts[0]["chrom"] == "chr1"
    assert transcripts[0]["utr3"]
    assert transcripts[0]["utr5"]
    assert transcripts[0]["exons"]
    assert transcripts[0]["cds"]


def test_get_nonexistant_gene_transcripts(
    anonymous_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = anonymous_client.get("/api/v3/genome/gene_models/default/asdf")

    assert response
    assert response.status_code == 404


def test_get_case_insensitive_gene(
    anonymous_client: Client,
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = anonymous_client.get("/api/v3/genome/gene_models/default/T4")
    assert response
    assert response.data["gene"] == "t4"  # type: ignore
    assert response.status_code == 200


def test_search_gene_symbols(
    anonymous_client: Client,
    t4c8_wgpf_instance: WGPFInstance,
    mocker: pytest_mock.MockFixture,
) -> None:

    mocker.patch.object(
        t4c8_wgpf_instance.gene_models,
        "gene_models",
        {
            "CHD3": [], "CHD2": [], "CHD8": [], "CHD1L": [], "CHD1": [],
            "CHD4": [], "CHD9": [], "CHD7": [], "CHD5": [], "CHDH": [],
            "CHD6": [], "CTEST": [], "CTEST2": [], "CTEST3": [], "CTEST4": [],
        },
    )

    response = anonymous_client.get("/api/v3/genome/gene_models/search/CHD8")
    assert response.data["gene_symbols"] == ["CHD8"]  # type: ignore

    response = anonymous_client.get("/api/v3/genome/gene_models/search/CHD")
    assert set(response.data["gene_symbols"]) == {  # type: ignore
        "CHD3", "CHD2", "CHD8", "CHD1L", "CHD1",
        "CHD4", "CHD9", "CHD7", "CHD5", "CHDH", "CHD6",
    }

    response = anonymous_client.get("/api/v3/genome/gene_models/search/C")
    assert len(response.data["gene_symbols"]) == 15  # type: ignore


def test_validate_gene_symbols(
    anonymous_client: Client,
    t4c8_wgpf_instance: WGPFInstance,
    mocker: pytest_mock.MockFixture,
) -> None:

    mocker.patch.object(
        t4c8_wgpf_instance.gene_models,
        "gene_models",
        {
            "CHD3": [], "CHD2": [], "CHD8": [], "CHD1L": [], "CHD1": [],
            "CHD4": [], "CHD9": [], "CHD7": [], "CHD5": [], "CHDH": [],
            "CHD6": [], "CTEST": [], "CTEST2": [], "CTEST3": [], "CTEST4": [],
        },
    )

    response = anonymous_client.post(
        "/api/v3/genome/gene_models/validate",
        json.dumps({
            "geneSymbols": [
                "CHD8",
                "CHDHA",  # Invalid gene symbol
                "CHD2",
                "CHD99",  # Invalid gene symbol
                "CTEST3",
                "CTEST99",  # Invalid gene symbol
            ],
        }),
        content_type="application/json",
    )
    assert response.data == ["CHDHA", "CHD99", "CTEST99"]  # type: ignore
