# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
import pytest

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance")


def test_default_gene_models_id(anonymous_client):
    response = anonymous_client.get("/api/v3/genome/gene_models/default")

    assert response
    assert response.status_code == 200
    assert response.data == \
        "hg19/GATK_ResourceBundle_5777_b37_phiX174_short/gene_models/" \
        "refGene_201309"
    #  "hg19/gene_models/refGene_v20190211"


def test_get_plcxd1_transcripts(anonymous_client):
    response = anonymous_client.get(
        "/api/v3/genome/gene_models/default/PLCXD1")

    assert response
    assert response.status_code == 200

    response_data = json.loads(response.content)
    assert response_data

    assert response_data["gene"] == "PLCXD1"
    transcripts = response_data["transcripts"]
    assert len(transcripts) == 2
    assert transcripts[0]["transcript_id"] == "NR_028057_1"
    assert transcripts[0]["strand"] == "+"
    assert transcripts[0]["chrom"] == "X"
    assert not transcripts[0]["utr3"]
    assert not transcripts[0]["utr5"]
    assert transcripts[0]["exons"]
    assert transcripts[0]["cds"]
    assert transcripts[1]["transcript_id"] == "NM_018390_1"
    assert transcripts[1]["strand"] == "+"
    assert transcripts[1]["chrom"] == "X"
    assert transcripts[1]["utr3"]
    assert transcripts[1]["utr5"]
    assert transcripts[1]["exons"]
    assert transcripts[1]["cds"]


def test_get_nonexistant_gene_transcripts(anonymous_client):
    response = anonymous_client.get("/api/v3/genome/gene_models/default/asdf")

    assert response
    assert response.status_code == 404


def test_get_case_insensitive_gene(anonymous_client):
    response = anonymous_client.get(
        "/api/v3/genome/gene_models/default/fAm110c")
    assert response.status_code == 200

    response_data = json.loads(response.content)
    assert response_data["gene"] == "FAM110C"


def test_search_gene_symbols(anonymous_client):
    response = anonymous_client.get("/api/v3/genome/gene_models/search/F")

    response = anonymous_client.get(
        "/api/v3/genome/gene_models/search/FAM110C")
    response_data = json.loads(response.content)
    assert response_data["gene_symbols"] == ["FAM110C"]

    response = anonymous_client.get("/api/v3/genome/gene_models/search/FAM13")
    response_data = json.loads(response.content)
    assert set(response_data["gene_symbols"]) == {"FAM138A", "FAM138F"}
