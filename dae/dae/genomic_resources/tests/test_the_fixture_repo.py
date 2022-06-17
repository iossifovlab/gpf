# pylint: disable=redefined-outer-name,C0114,C0116,protected-access

from dae.genomic_resources.fsspec_protocol import build_fsspec_protocol
from dae.genomic_resources.repository import GenomicResourceRepo


def test_genomic_resources_fixture(fixture_dirname):
    dirname = fixture_dirname("genomic_resources")
    proto = build_fsspec_protocol("d", dirname)
    repo = GenomicResourceRepo(proto)

    all_resources = list(repo.get_all_resources())
    assert len(all_resources) > 0
    basic_resources = [
        r for r in all_resources
    ]
    assert len(basic_resources) == len(all_resources)
