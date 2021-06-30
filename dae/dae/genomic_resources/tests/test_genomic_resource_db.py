from dae.genomic_resources.resource_db import GenomicResourceDB


def test_basic(test_grdb_config):
    grdb = GenomicResourceDB(test_grdb_config)
    repo = grdb.repositories[0]
    print(repo.get_name())
    print(repo.get_url())
    for resource in repo.top_level_group.get_resources():
        print("ID")
        print(resource.get_id())
        print("URL")
        print(resource.get_url())
        print(resource.get_manifest())
        print("===")


def test_http(resources_http_server, test_grdb_http_config):
    grdb = GenomicResourceDB(test_grdb_http_config)
    repo = grdb.repositories[0]
    print(repo.get_name())
    print(repo.get_url())
    for resource in repo.top_level_group.get_resources():
        print("ID")
        print(resource.get_id())
        print("URL")
        print(resource.get_url())
        print(resource.get_manifest())
        print(resource.get_config())
        print("=============")
        print("=============")
        print("=============")
        print("=============")
