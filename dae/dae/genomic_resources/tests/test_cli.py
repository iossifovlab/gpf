from dae.genomic_resources.embeded_repository import GenomicResourceEmbededRepo
from dae.genomic_resources.dir_repository import GenomicResourceDirRepo
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.repository import GRP_CONTENTS_FILE_NAME
from dae.genomic_resources.cli import cli_manage


def test_cli_manage(tmp_path):

    demo_gtf_content = "TP53\tchr3\t300\t200".encode('utf-8')
    src_repo = GenomicResourceEmbededRepo("src", content={
        "one": {
            GR_CONF_FILE_NAME: "",
            "data.txt": "alabala"
        },
        "sub": {
            "two[1.0]": {
                GR_CONF_FILE_NAME: "type: gene_models\nfile: genes.gtf",
                "genes.txt": demo_gtf_content
            }
        }
    })
    dir_repo = GenomicResourceDirRepo('dir', directory=tmp_path)
    dir_repo.store_all_resources(src_repo)

    assert not (tmp_path / GRP_CONTENTS_FILE_NAME).is_file()
    cli_manage(["index", str(tmp_path)])
    assert (tmp_path / GRP_CONTENTS_FILE_NAME).is_file()
