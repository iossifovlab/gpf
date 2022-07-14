# pylint: disable=W0621,C0114,C0116,W0212,W0613

from dae.genomic_resources.fsspec_protocol import build_fsspec_protocol
from dae.genomic_resources.repository import GenomicResourceProtocolRepo


def test_genomic_resources_fixture(fixture_dirname):
    dirname = fixture_dirname("genomic_resources")
    proto = build_fsspec_protocol("d", dirname)
    repo = GenomicResourceProtocolRepo(proto)

    all_resources = list(repo.get_all_resources())
    assert len(all_resources) > 0
