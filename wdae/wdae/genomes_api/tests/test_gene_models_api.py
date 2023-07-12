# pylint: disable=W0621,C0114,C0116,W0212,W0613

def test_default_gene_models_id(anonymous_client):
    response = anonymous_client.get("/api/v3/genome/gene_models/default")

    assert response
    assert response.status_code == 200
    assert response.data == \
        "hg19/gene_models/refGene_v20190211"


def test_get_chd8_transcripts(anonymous_client):
    response = anonymous_client.get("/api/v3/genome/gene_models/default/CHD8")

    assert response
    assert response.status_code == 200
    assert response.data
    assert response.data["gene"] == "CHD8"
    transcripts = response.data["transcripts"]
    assert len(transcripts) == 2
    assert transcripts[0]["transcript_id"] == "NM_001170629_1"
    assert transcripts[0]["strand"] == "-"
    assert transcripts[0]["chrom"] == "14"
    assert transcripts[0]["utr3"]
    assert transcripts[0]["utr5"]
    assert transcripts[0]["exons"]
    assert transcripts[0]["cds"]
    assert transcripts[1]["transcript_id"] == "NM_020920_1"
    assert transcripts[1]["strand"] == "-"
    assert transcripts[1]["chrom"] == "14"
    assert transcripts[1]["utr3"]
    assert transcripts[1]["utr5"]
    assert transcripts[1]["exons"]
    assert transcripts[1]["cds"]


def test_get_nonexistant_gene_transcripts(anonymous_client):
    response = anonymous_client.get("/api/v3/genome/gene_models/default/asdf")

    assert response
    assert response.status_code == 404

def test_get_case_insensitive_gene(anonymous_client):
    response = anonymous_client.get("/api/v3/genome/gene_models/default/cHd8")

    assert response
    assert response.status_code == 200

def test_search_gene_symbols(anonymous_client):
    response = anonymous_client.get("/api/v3/genome/gene_models/search/CHD8")
    assert response.data["gene_symbols"] == ["CHD8"]

    response = anonymous_client.get("/api/v3/genome/gene_models/search/CHD")
    assert set(response.data["gene_symbols"]) == {
        "CHD3", "CHD2", "CHD8", "CHD1L", "CHD1",
        "CHD4", "CHD9", "CHD7", "CHD5", "CHDH", "CHD6"
    }

    response = anonymous_client.get("/api/v3/genome/gene_models/search/C")
    assert len(response.data["gene_symbols"]) <= 20
