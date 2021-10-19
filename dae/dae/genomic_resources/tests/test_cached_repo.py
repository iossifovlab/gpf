from dae.genomic_resources.cached_repository import GenomicResourceCachedRepo
from dae.genomic_resources.embeded_repository import GenomicResourceEmbededRepo
from dae.genomic_resources import build_genomic_resource_repository


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
