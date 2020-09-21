
def test_default_gene_models_id(admin_client):
    response = admin_client.get("/api/v3/genome/gene_models/default")

    assert response
    assert response.status_code == 200
    assert response.data == "RefSeq"


def test_get_chd8_transcripts(admin_client):
    response = admin_client.get("/api/v3/genome/gene_models/default/CHD8")

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


def test_get_nonexistant_gene_transcripts(admin_client):
    response = admin_client.get("/api/v3/genome/gene_models/default/asdf")

    assert response
    assert response.status_code == 404
