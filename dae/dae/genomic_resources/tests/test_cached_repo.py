from dae.genomic_resources.cached_repository import GenomicResourceCachedRepo
from dae.genomic_resources.embeded_repository import GenomicResourceEmbededRepo
from dae.genomic_resources import build_genomic_resource_repository


def test_create_definition_with_cache(tmpdir):
    repo = build_genomic_resource_repository(
        {"cacheDir": tmpdir, "id": "bla", "type": "embeded",
         "content": {
             "one": {"genomic_resrouce.yaml"}
         }})
    assert isinstance(repo, GenomicResourceCachedRepo)


def test_get_cached_resource(tmpdir):
    chRepo = GenomicResourceEmbededRepo(
        "bla", {"one": {"genomic_resource.yaml": ""}})
    repo = GenomicResourceCachedRepo(chRepo, tmpdir)

    print("BBBB", tmpdir)
    print("BBBB", list(chRepo.get_all_resources()))

    gr = repo.get_resource("one")
    assert gr
    # print("BBBBB", gr.repo.__class__)
