# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import Any, Generator

import pytest

from dae.genomic_resources.cached_repository import \
    CachingProtocol
from dae.genomic_resources.testing import \
    FsspecReadWriteProtocol, \
    build_inmemory_test_protocol, \
    build_filesystem_test_protocol, \
    build_s3_test_protocol, \
    setup_directories, setup_tabix


def test_caching_repo_simple(
        content_fixture: dict[str, Any],
        tmp_path_factory: pytest.TempPathFactory) -> None:

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
def remote_proto_fixture(
    content_fixture: dict[str, Any],
    tmp_path_factory: pytest.TempPathFactory
) -> FsspecReadWriteProtocol:
    root_path = tmp_path_factory.mktemp("source_proto_fixture")
    setup_directories(root_path, content_fixture)
    setup_tabix(
        root_path / "one" / "test.txt.gz",
        """
            #chrom  pos_begin  pos_end    c1
            1      1          10         1.0
            2      1          10         2.0
            2      11         20         2.5
            3      1          10         3.0
            3      11         20         3.5
        """,
        seq_col=0, start_col=1, end_col=2)
    proto = build_filesystem_test_protocol(root_path)
    return proto


# @pytest.fixture(params=["file", "s3"])
@pytest.fixture(params=["file"])
def caching_proto(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
    remote_proto_fixture: FsspecReadWriteProtocol
) -> Generator[CachingProtocol, None, None]:

    remote_proto = remote_proto_fixture
    caching_scheme = request.param

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


def test_get_resource_three(
        caching_proto: CachingProtocol) -> None:
    proto = caching_proto
    res = proto.get_resource("three")

    assert res.resource_id == "three"
    assert res.version == (2, 0)


def test_get_resource_two(
        caching_proto: CachingProtocol) -> None:
    res = caching_proto.get_resource("sub/two")

    assert res.resource_id == "sub/two"
    assert res.version == (1, 0)


def test_get_resource_copies_nothing_three(
        caching_proto: CachingProtocol) -> None:
    res = caching_proto.get_resource("three")

    local_proto = caching_proto.local_protocol
    assert not local_proto.file_exists(res, "genomic_resource.yaml")
    assert not local_proto.file_exists(res, "sub1/a.txt")
    assert not local_proto.file_exists(res, "sub2/b.txt")


def test_get_resource_copies_nothing_two(
        caching_proto: CachingProtocol) -> None:
    res = caching_proto.get_resource("sub/two")

    local_proto = caching_proto.local_protocol
    assert not local_proto.file_exists(res, "genomic_resource.yaml")
    assert not local_proto.file_exists(res, "genes.gtf")


def test_open_raw_file_copies_the_file_three_a(
        caching_proto: CachingProtocol) -> None:

    res = caching_proto.get_resource("three")
    with caching_proto.open_raw_file(res, "sub1/a.txt") as infile:
        content = infile.read()
    assert content == "a"

    local_proto = caching_proto.local_protocol
    assert local_proto.file_exists(res, "sub1/a.txt")
    assert not local_proto.file_exists(res, "genomic_resource.yaml")
    assert not local_proto.file_exists(res, "sub2/b.txt")


def test_open_raw_file_copies_the_file_three_b(
        caching_proto: CachingProtocol) -> None:
    res = caching_proto.get_resource("three")
    with caching_proto.open_raw_file(res, "sub2/b.txt") as infile:
        content = infile.read()
    assert content == "b"

    local_proto = caching_proto.local_protocol
    assert local_proto.file_exists(res, "sub2/b.txt")
    assert not local_proto.file_exists(res, "genomic_resource.yaml")
    assert not local_proto.file_exists(res, "sub1/a.txt")


def test_open_tabix_file_simple(
        caching_proto: CachingProtocol) -> None:
    res = caching_proto.get_resource("one")
    with caching_proto.open_tabix_file(res, "test.txt.gz") as tabix:
        assert tabix.contigs == ["1", "2", "3"]
