# pylint: disable=redefined-outer-name,C0114,C0116,protected-access
import pytest

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


@pytest.fixture
def caching_proto(embedded_proto, tmp_path):

    remote_proto = embedded_proto(tmp_path / "source")
    local_proto = build_embedded_protocol(
        "local", str(tmp_path / "cache"), {})

    proto = CachingProtocol("test_cache", remote_proto, local_proto)
    return proto


def test_get_resource_three(caching_proto):

    res = caching_proto.get_resource("three")

    assert res.resource_id == "three"
    assert res.version == (2, 0)


def test_get_resource_two(caching_proto):

    res = caching_proto.get_resource("sub/two")

    assert res.resource_id == "sub/two"
    assert res.version == (1, 0)


def test_get_resource_copies_only_resource_config_three(caching_proto):

    res = caching_proto.get_resource("three")

    local_proto = caching_proto.local_protocol
    assert local_proto.file_exists(res, "genomic_resource.yaml")
    assert not local_proto.file_exists(res, "sub1/a.txt")
    assert not local_proto.file_exists(res, "sub2/b.txt")


def test_get_resource_copies_only_resource_config_two(caching_proto):

    res = caching_proto.get_resource("sub/two")

    local_proto = caching_proto.local_protocol
    assert local_proto.file_exists(res, "genomic_resource.yaml")
    assert not local_proto.file_exists(res, "genes.gtf")


def test_open_raw_file_copies_the_file_three_a(caching_proto):

    res = caching_proto.get_resource("three")
    with caching_proto.open_raw_file(res, "sub1/a.txt") as infile:
        content = infile.read()
    assert content == "a"

    local_proto = caching_proto.local_protocol
    assert local_proto.file_exists(res, "genomic_resource.yaml")
    assert local_proto.file_exists(res, "sub1/a.txt")
    assert not local_proto.file_exists(res, "sub2/b.txt")


def test_open_raw_file_copies_the_file_three_b(caching_proto):

    res = caching_proto.get_resource("three")
    with caching_proto.open_raw_file(res, "sub2/b.txt") as infile:
        content = infile.read()
    assert content == "b"

    local_proto = caching_proto.local_protocol
    assert local_proto.file_exists(res, "genomic_resource.yaml")
    assert local_proto.file_exists(res, "sub2/b.txt")
    assert not local_proto.file_exists(res, "sub1/a.txt")
