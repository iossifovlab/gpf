from dae.genomic_resources.cached_repository import GenomicResourceCachedRepo
from dae.genomic_resources.embeded_repository import GenomicResourceEmbededRepo
from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.repository import GR_CONF_FILE_NAME


def test_create_definition_with_cache(tmpdir):
    repo = build_genomic_resource_repository(
        {"cache_dir": tmpdir, "id": "bla", "type": "embeded",
         "content": {
             "one": {"genomic_resrouce.yaml"}
         }})
    assert isinstance(repo, GenomicResourceCachedRepo)


def test_get_cached_resource(tmpdir):
    child_repo = GenomicResourceEmbededRepo(
        "bla", {"one": {"genomic_resource.yaml": ""}})
    repo = GenomicResourceCachedRepo(child_repo, tmpdir)

    gr = repo.get_resource("one")
    assert gr


def test_cached_get_all_resources(tmpdir):

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

    cache_repo = GenomicResourceCachedRepo(src_repo, tmpdir)
    assert len(list(cache_repo.get_all_resources())) == 0

    src_gr = src_repo.get_resource("sub/two")
    cache_gr = cache_repo.get_resource("sub/two")

    assert src_gr.get_manifest() == cache_gr.get_manifest()
    assert src_gr.get_manifest() == cache_gr.build_manifest()

    assert len(list(cache_repo.get_all_resources())) == 1
