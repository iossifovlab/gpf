from dae.genomic_resources.resource_db import GenomicResourceDB


def test_fs_repository(test_grdb_config, fixture_dirname):
    grdb = GenomicResourceDB(test_grdb_config)
    assert len(grdb.repositories) == 1
    repo = grdb.repositories[0]
    print(repo.get_name())
    print(repo.get_url())
    resources = list(repo.top_level_group.get_resources())
    resources.sort(key=lambda x: x.get_id())
    assert resources[0].get_id() == "hg38/TESTCADD"
    assert resources[0].get_url() == \
        "file://" + fixture_dirname("genomic_scores/hg38/TESTCADD")
    assert resources[1].get_id() == "hg38/TESTFreq"
    assert resources[1].get_url() == \
        "file://" + fixture_dirname("genomic_scores/hg38/TESTFreq")
    assert resources[2].get_id() == "hg38/TESTphastCons100way"
    assert resources[2].get_url() == \
        "file://" + fixture_dirname("genomic_scores/hg38/TESTphastCons100way")


def test_cache_filesystem(test_grdb_config):
    grdb = GenomicResourceDB(test_grdb_config)
    grdb.cache_resource("hg38/TESTCADD")
    testcadd = grdb._cache.get_resource("hg38/TESTCADD")
    assert testcadd is not None


def test_cache_http(resources_http_server, test_grdb_http_config):
    grdb = GenomicResourceDB(test_grdb_http_config)
    grdb.cache_resource("hg38/TESTCADD")
    testcadd = grdb._cache.get_resource("hg38/TESTCADD")
    assert testcadd is not None


def test_http_repository(resources_http_server, test_grdb_http_config):
    grdb = GenomicResourceDB(test_grdb_http_config)
    assert len(grdb.repositories) == 1
    repo = grdb.repositories[0]
    print(repo.get_name())
    print(repo.get_url())
    resources = list(repo.top_level_group.get_resources())
    resources.sort(key=lambda x: x.get_id())
    assert resources[0].get_id() == "hg38/TESTCADD"
    assert resources[0].get_url() == "http://localhost:16200/hg38/TESTCADD"
    assert resources[1].get_id() == "hg38/TESTFreq"
    assert resources[1].get_url() == "http://localhost:16200/hg38/TESTFreq"
    assert resources[2].get_id() == "hg38/TESTphastCons100way"
    assert resources[2].get_url() == \
        "http://localhost:16200/hg38/TESTphastCons100way"
