# pylint: disable=W0621,C0114,C0116,W0212,W0613
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
    t4c8_wgpf_instance: WGPFInstance,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    response = anonymous_client.get("/api/v3/genome/gene_models/search/t4")
    assert response.data["gene_symbols"] == ["t4"]  # type: ignore
    response = anonymous_client.get("/api/v3/genome/gene_models/search/t")
    assert response.data["gene_symbols"] == ["t4"]  # type: ignore
