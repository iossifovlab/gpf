from dae.genomic_resources.dir_repository import GenomicResourceDirRepo


def test_genomic_resources_fixture(fixture_dirname):
    dirname = fixture_dirname("genomic_resources")

    repo = GenomicResourceDirRepo('d', dirname)

    all_resources = list(repo.get_all_resources())
    assert len(all_resources) > 0
    basic_resources = [
        r for r in all_resources
    ]
    assert len(basic_resources) == len(all_resources)
