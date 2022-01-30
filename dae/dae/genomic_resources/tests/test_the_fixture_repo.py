from dae.genomic_resources.dir_repository import GenomicResourceDirRepo


def test_genomic_resources_fixture(fixture_dirname):
    dr = fixture_dirname("genomic_resources")

    repo = GenomicResourceDirRepo('d', dr)

    all_resources = list(repo.get_all_resources())
    assert len(all_resources) > 0
    basic_resources = [
        r for r in all_resources if r.get_resource_type() == "Basic"]
    assert len(basic_resources) == len(all_resources)
