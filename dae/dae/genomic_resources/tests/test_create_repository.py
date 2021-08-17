
from dae.genomic_resources.repository import \
    create_genomic_resources_repository, \
    walk_genomic_resources_repository


def test_create_genomic_resources_repository(fixture_dirname):
    repo_dirname = fixture_dirname("genomic_resources")
    print(repo_dirname)

    create_genomic_resources_repository(repo_dirname)


def test_walk_genomic_resources_repository(fixture_dirname):
    repo_dirname = fixture_dirname("genomic_resources")
    print(repo_dirname)

    walk_genomic_resources_repository(repo_dirname)
