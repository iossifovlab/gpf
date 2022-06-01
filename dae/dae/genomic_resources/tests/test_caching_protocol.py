# pylint: disable=redefined-outer-name,C0114,C0116,protected-access

from dae.genomic_resources.embedded_protocol import \
    build_embedded_protocol
from dae.genomic_resources.caching_protocol import \
    CachingProtocol


def test_caching_repo_simple(embedded_proto, tmp_path):

    local_proto = build_embedded_protocol(
        "local", str(tmp_path / "cache"), {})

    assert local_proto is not None
    assert len(list(local_proto.get_all_resources())) == 0

    remote_proto = embedded_proto(tmp_path / "source")
    assert len(list(remote_proto.get_all_resources())) == 4

    caching_proto = CachingProtocol("cache", remote_proto, local_proto)
    assert caching_proto is not None

    assert len(list(caching_proto.get_all_resources())) == 4
