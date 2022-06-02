# pylint: disable=redefined-outer-name,C0114,C0116,protected-access,no-member

import pytest

from dae.genomic_resources.fsspec_protocol import \
    build_fsspec_protocol
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
    assert len(list(remote_proto.get_all_resources())) == 5

    caching_proto = CachingProtocol("cache", remote_proto, local_proto)
    assert caching_proto is not None

    assert len(list(caching_proto.get_all_resources())) == 5


@pytest.fixture
def caching_proto(
        embedded_proto, tmp_path, s3_base):  # pylint: disable=unused-argument

    def builder(caching_scheme="file"):
        remote_proto = embedded_proto(tmp_path / "source")

        if caching_scheme == "file":
            caching_proto = build_fsspec_protocol(
                "local", str(tmp_path / "cache"))
        elif caching_scheme == "s3":
            # pylint: disable=import-outside-toplevel
            from botocore.session import Session  # type: ignore
            endpoint_url = "http://127.0.0.1:5555/"
            # NB: we use the sync botocore client for setup
            session = Session()
            client = session.create_client("s3", endpoint_url=endpoint_url)
            client.create_bucket(Bucket="test-bucket", ACL="public-read")

            caching_proto = build_fsspec_protocol(
                "local",
                f"s3://test-bucket{tmp_path}",
                endpoint_url=endpoint_url
            )
        else:
            raise ValueError(f"Unsupported caching scheme: {caching_scheme}")

        proto = CachingProtocol("test_cache", remote_proto, caching_proto)
        return proto

    return builder


@pytest.mark.parametrize("caching_scheme", [
    "file",
    "s3",
])
def test_get_resource_three(caching_proto, caching_scheme):
    proto = caching_proto(caching_scheme)
    res = proto.get_resource("three")

    assert res.resource_id == "three"
    assert res.version == (2, 0)


@pytest.mark.parametrize("caching_scheme", [
    "file",
    "s3",
])
def test_get_resource_two(caching_proto, caching_scheme):
    proto = caching_proto(caching_scheme)
    res = proto.get_resource("sub/two")

    assert res.resource_id == "sub/two"
    assert res.version == (1, 0)


@pytest.mark.parametrize("caching_scheme", [
    "file",
    "s3",
])
def test_get_resource_copies_only_resource_config_three(
        caching_proto, caching_scheme):
    proto = caching_proto(caching_scheme)
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
    proto = caching_proto(caching_scheme)
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

    proto = caching_proto(caching_scheme)
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
def test_open_raw_file_copies_the_file_three_b(caching_proto, caching_scheme):
    proto = caching_proto(caching_scheme)
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
    proto = caching_proto(caching_scheme)

    res = proto.get_resource("one")
    with proto.open_tabix_file(res, "test.txt.gz") as tabix:
        assert tabix.contigs == ["1", "2", "3"]
