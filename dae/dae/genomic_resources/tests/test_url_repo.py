# pylint: disable=redefined-outer-name,C0114,C0116,protected-access
from dae.genomic_resources.repository import GR_CONF_FILE_NAME


def test_url_vs_dir_results(repo_testing):

    content = {
        "one": {
            GR_CONF_FILE_NAME: "",
            "data.txt": "alabala"
        },
        "sub": {
            "two(1.0)": {
                GR_CONF_FILE_NAME: "type: gene_models\nfile: genes.gtf",
                "genes.txt": "TP53\tchr3\t300\t200"
            }
        }
    }    
    dir_repo = repo_testing(repo_id="src", scheme="file", content=content)
    url_repo = repo_testing(repo_id="url", scheme="http", content=content)

    def resource_set(repo):
        return {
            (gr.resource_id, gr.version) for gr in repo.get_all_resources()
        }

    assert dir_repo and url_repo
    assert resource_set(dir_repo) == resource_set(url_repo)
    assert url_repo.get_resource("sub/two").get_file_content("genes.txt") == \
        "TP53\tchr3\t300\t200"
