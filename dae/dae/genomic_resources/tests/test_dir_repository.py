from dae.genomic_resources.embeded_repository import GenomicResourceEmbededRepo
from dae.genomic_resources.dir_repository import GenomicResourceDirRepo
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources import GeneModelsResource


def test_dir_repository(tmp_path):

    demo_gtf_content = "TP53\tchr3\t300\t200".encode('utf-8')
    src_repo = GenomicResourceEmbededRepo("src", content={
        "one": {
            GR_CONF_FILE_NAME: "",
            "data.txt": "alabala"
        },
        "sub": {
            "two[1.0]": {
                GR_CONF_FILE_NAME: "type: GeneModels\nfile: genes.gtf",
                "genes.txt": demo_gtf_content
            }
        }
    })
    dir_repo = GenomicResourceDirRepo('dir', directory=tmp_path)
    dir_repo.store_all_resources(src_repo)

    def resource_set(repo):
        return {(gr.resource_id, gr.version) for gr in repo.get_all_resources()}

    assert resource_set(src_repo) == resource_set(dir_repo)
    assert isinstance(dir_repo.get_resource("sub/two"), GeneModelsResource)
    assert dir_repo.get_resource("sub/two").get_file_content("genes.txt") == \
        demo_gtf_content
