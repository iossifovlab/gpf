from dae.genomic_resources.embeded_repository import GenomicResourceEmbededRepo
from dae.genomic_resources.dir_repository import GenomicResourceDirRepo
from dae.genomic_resources.url_repository import GenomicResourceURLRepo
from dae.genomic_resources.repository import GR_CONF_FILE_NAME


def test_url_vs_dir_results(tmp_path):

    test_repo_URL = "file://" + str(tmp_path)
    demo_gtf_content = "TP53\tchr3\t300\t200"
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
    dir_repo.save_content_file()
    url_repo = GenomicResourceURLRepo("url", url=test_repo_URL)

    def resource_set(repo):
        return {
            (gr.resource_id, gr.version) for gr in repo.get_all_resources()
        }

    assert dir_repo and url_repo
    assert resource_set(src_repo) == resource_set(url_repo)
    assert url_repo.get_resource("sub/two").get_file_content("genes.txt") == \
        demo_gtf_content
