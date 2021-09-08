from dae.genomic_resources.repository import FSGenomicResourcesRepo, \
    GenomicResourcesRepoCache


def test_cache_resource_repository(test_grdb_config, temp_dirname_grdb):
    repo_config = test_grdb_config["genomic_resource_repositories"][0]
    grr_id = repo_config.id
    grr_url = repo_config.url

    repo = FSGenomicResourcesRepo(grr_id, grr_url)
    repo.load()

    assert repo is not None

    cached_repo = GenomicResourcesRepoCache(repo, temp_dirname_grdb)
    assert cached_repo is not None

    assert not cached_repo.is_cached("hg38/TESTCADD")

    resource = cached_repo.get_resource("hg38/TESTCADD")
    assert resource is not None
    assert resource.resource_id == "hg38/TESTCADD"

    assert cached_repo.is_cached("hg38/TESTCADD")
