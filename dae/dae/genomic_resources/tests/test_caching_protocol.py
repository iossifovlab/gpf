# pylint: disable=W0621,C0114,C0116,W0212,W0613
import contextlib

import pytest

from dae.genomic_resources.cached_repository import \
    CachingProtocol
from dae.genomic_resources.testing import \
    build_inmemory_test_protocol, \
    build_filesystem_test_protocol, \
    build_s3_test_protocol


def test_caching_repo_simple(content_fixture, tmp_path_factory):

    local_proto = build_filesystem_test_protocol(
        tmp_path_factory.mktemp("cache_proto_test"))

    assert local_proto is not None
    assert len(list(local_proto.get_all_resources())) == 0

    remote_proto = build_inmemory_test_protocol(content_fixture)
    assert len(list(remote_proto.get_all_resources())) == 5

    caching_proto = CachingProtocol(remote_proto, local_proto)
    assert caching_proto is not None

    assert len(list(caching_proto.get_all_resources())) == 5


@pytest.fixture
def caching_proto(tmp_path_factory, src_proto_fixture):

    @contextlib.contextmanager
    def builder(caching_scheme):
        remote_proto = src_proto_fixture

        if caching_scheme == "file":
            root_path = tmp_path_factory.mktemp("file_caching_proto_path")
            caching_proto = build_filesystem_test_protocol(root_path)
            yield CachingProtocol(remote_proto, caching_proto)

        elif caching_scheme == "s3":
            root_path = tmp_path_factory.mktemp("s3_caching_proto_path")
            with build_s3_test_protocol(root_path) as caching_proto:
                yield CachingProtocol(remote_proto, caching_proto)

        else:
            raise ValueError(f"Unsupported caching scheme: {caching_scheme}")

    return builder


@pytest.mark.parametrize("caching_scheme", [
    "file",
    "s3",
])
def test_get_resource_three(caching_proto, caching_scheme):
    with caching_proto(caching_scheme) as proto:
        res = proto.get_resource("three")

        assert res.resource_id == "three"
        assert res.version == (2, 0)


@pytest.mark.parametrize("caching_scheme", [
    "file",
    "s3",
])
def test_get_resource_two(caching_proto, caching_scheme):
    with caching_proto(caching_scheme) as proto:
        res = proto.get_resource("sub/two")

        assert res.resource_id == "sub/two"
        assert res.version == (1, 0)


@pytest.mark.parametrize("caching_scheme", [
    "file",
    "s3",
])
def test_get_resource_copies_only_resource_config_three(
        caching_proto, caching_scheme):
    with caching_proto(caching_scheme) as proto:
        res = proto.get_resource("three")

        local_proto = proto.local_protocol
        assert local_proto.file_exists(res, "genomic_resource.yaml")
        assert not local_proto.file_exists(res, "sub1/a.txt")
        assert not local_proto.file_exists(res, "sub2/b.txt")


@pytest.mark.parametrize("caching_scheme", [
    "file",
    "s3",
])
def test_get_resource_copies_only_resource_config_two(
        caching_proto, caching_scheme):
    with caching_proto(caching_scheme) as proto:
        res = proto.get_resource("sub/two")

        local_proto = proto.local_protocol
        assert local_proto.file_exists(res, "genomic_resource.yaml")
        assert not local_proto.file_exists(res, "genes.gtf")


@pytest.mark.parametrize("caching_scheme", [
    "file",
    "s3",
])
def test_open_raw_file_copies_the_file_three_a(
        caching_proto, caching_scheme):

    with caching_proto(caching_scheme) as proto:
        res = proto.get_resource("three")
        with proto.open_raw_file(res, "sub1/a.txt") as infile:
            content = infile.read()
        assert content == "a"

        local_proto = proto.local_protocol
        assert local_proto.file_exists(res, "genomic_resource.yaml")
        assert local_proto.file_exists(res, "sub1/a.txt")
        assert not local_proto.file_exists(res, "sub2/b.txt")


@pytest.mark.parametrize("caching_scheme", [
    "file",
    "s3",
])
def test_open_raw_file_copies_the_file_three_b(
        caching_proto, caching_scheme):
    with caching_proto(caching_scheme) as proto:
        res = proto.get_resource("three")
        with proto.open_raw_file(res, "sub2/b.txt") as infile:
            content = infile.read()
        assert content == "b"

        local_proto = proto.local_protocol
        assert local_proto.file_exists(res, "genomic_resource.yaml")
        assert local_proto.file_exists(res, "sub2/b.txt")
        assert not local_proto.file_exists(res, "sub1/a.txt")


@pytest.mark.parametrize("caching_scheme", [
    "file",
    "s3",
])
def test_open_tabix_file_simple(
        caching_proto, caching_scheme):
    with caching_proto(caching_scheme) as proto:

        res = proto.get_resource("one")
        with proto.open_tabix_file(res, "test.txt.gz") as tabix:
            assert tabix.contigs == ["1", "2", "3"]
