from dae.genomic_resources.resource_db import GenomicResourceDB, \
    CachedGenomicResourceDB


def test_fs_repository(test_grdb_config, fixture_dirname):
    grdb = GenomicResourceDB(
        test_grdb_config["genomic_resource_repositories"])
    assert len(grdb.repositories) == 1
    repo = grdb.repositories[0]
    print(repo.get_name())
    print(repo.get_url())
    resources = list(repo.top_level_group.get_resources())
    resources.sort(key=lambda x: x.get_id())
    print(resources)

    resource = repo.get_resource("hg38/TESTCADD")
    assert resource.get_id() == "hg38/TESTCADD"
    assert resource.get_url() == \
        f"file://{fixture_dirname('genomic_resources/hg38/TESTCADD')}"

    # resource = repo.get_resource("hg38/TESTFreq")
    # assert resource.get_id() == "hg38/TESTFreq"
    # assert resource.get_url() == \
    #     f"file://{fixture_dirname('genomic_resources/hg38/TESTFreq')}"

    resource = repo.get_resource("hg38/TESTphastCons100way")
    assert resource.get_id() == "hg38/TESTphastCons100way"
    assert resource.get_url() == \
        f"file://{fixture_dirname('genomic_resources/hg38/TESTphastCons100way')}"


def test_cache_filesystem(test_grdb_config):
    grdb = CachedGenomicResourceDB(
        test_grdb_config["genomic_resource_repositories"],
        test_grdb_config["cache_location"])

    grdb.cache_resource("hg38/TESTCADD")
    testcadd = grdb._cache.get_resource("hg38/TESTCADD")
    assert testcadd is not None


def test_cache_http(resources_http_server, test_grdb_http_config):
    grdb = CachedGenomicResourceDB(
        test_grdb_http_config["genomic_resource_repositories"],
        test_grdb_http_config["cache_location"])
    grdb.cache_resource("hg38/TESTCADD")
    testcadd = grdb._cache.get_resource("hg38/TESTCADD")
    assert testcadd is not None


def test_http_repository(resources_http_server, test_grdb_http_config):
    grdb = CachedGenomicResourceDB(
        test_grdb_http_config["genomic_resource_repositories"],
        test_grdb_http_config["cache_location"])
    assert len(grdb.repositories) == 1
    repo = grdb.repositories[0]
    print(repo.get_name())
    print(repo.get_url())

    resources = list(repo.top_level_group.get_resources())
    resources.sort(key=lambda x: x.get_id())

    resource = repo.get_resource("hg38/TESTCADD")
    assert resource.get_id() == "hg38/TESTCADD"
    assert resource.get_url() == "http://localhost:16200/hg38/TESTCADD"

    # resource = repo.get_resource("hg38/TESTFreq")
    # assert resource.get_id() == "hg38/TESTFreq"
    # assert resource.get_url() == "http://localhost:16200/hg38/TESTFreq"

    resource = repo.get_resource("hg38/TESTphastCons100way")
    assert resource.get_id() == "hg38/TESTphastCons100way"
    assert resource.get_url() == \
        "http://localhost:16200/hg38/TESTphastCons100way"

    # assert resources[0].get_id() == "hg38/TESTCADD"
    # assert resources[0].get_url() == "http://localhost:16200/hg38/TESTCADD"
    # assert resources[1].get_id() == "hg38/TESTFreq"
    # assert resources[1].get_url() == "http://localhost:16200/hg38/TESTFreq"
    # assert resources[2].get_id() == "hg38/TESTphastCons100way"
    # assert resources[2].get_url() == \
    #     "http://localhost:16200/hg38/TESTphastCons100way"
