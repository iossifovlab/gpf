from dae.genomic_resources.embeded_repository import GenomicResourceEmbededRepo
from dae.genomic_resources.repository import GR_CONF_FILE_NAME


def test_embedded_repository_file_exists(tmp_path):
    repo = GenomicResourceEmbededRepo("src", content={
        "one": {
            GR_CONF_FILE_NAME: "",
            "data.txt": "alabala",
            "alabala.txt": "alabala",
        },
    })

    res = repo.get_resource("one")
    assert repo.file_exists(res, GR_CONF_FILE_NAME)
    assert not repo.file_exists(res, "missing_file")
    assert res.file_exists("data.txt")
