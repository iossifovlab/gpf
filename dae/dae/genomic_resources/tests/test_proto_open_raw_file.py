# pylint: disable=W0621,C0114,C0116,W0212,W0613

import gzip
import pytest

from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.testing import build_inmemory_test_protocol, \
    build_filesystem_test_protocol, s3_test_protocol, \
    build_http_test_protocol, copy_proto_genomic_resources


BREH_GZ = gzip.compress(b"breh")


@pytest.fixture(params=["file", "s3", "http", "inmemory"])
def fsspec_proto(
        request, content_fixture, tmp_path_factory, s3_server_fixture):

    src_proto = build_inmemory_test_protocol(
        content={
            "one": {
                GR_CONF_FILE_NAME: "opaa",
                "data.txt": "breh",
                "data.txt.gz": BREH_GZ
            }
        })

    scheme = request.param
    if scheme == "file":
        root_path = tmp_path_factory.mktemp("fsspec_proto_file")
        proto = build_filesystem_test_protocol(root_path)
        copy_proto_genomic_resources(proto, src_proto)
        yield proto
        return
    if scheme == "s3":
        proto = s3_test_protocol(s3_server_fixture)
        copy_proto_genomic_resources(
            proto,
            src_proto)
        yield proto
        return
    if scheme == "http":
        root_path = tmp_path_factory.mktemp("fsspec_proto_http")
        fs_proto = build_filesystem_test_protocol(root_path)
        copy_proto_genomic_resources(fs_proto, src_proto)
        with build_http_test_protocol(root_path) as http_proto:
            yield http_proto
        return
    if scheme == "inmemory":
        yield src_proto
        return
    raise ValueError(f"unexpected protocol scheme: <{scheme}>")


def test_open_raw_files(fsspec_proto):
    res = fsspec_proto.get_resource("one")
    files = sorted([fname for fname, _ in res.get_manifest().get_files()])
    assert files == ["data.txt", "data.txt.gz", GR_CONF_FILE_NAME]

    with res.open_raw_file("data.txt", "rt") as infile:
        content = infile.read(10)
        assert content == "breh"

    with res.open_raw_file("data.txt", "rb") as infile:
        content = infile.read(10)
        assert content == b"breh"

    with res.open_raw_file("data.txt.gz", "rb") as infile:
        content = infile.read()
        assert content == BREH_GZ

    with res.open_raw_file("data.txt.gz", "rt", compression=True) as infile:
        content = infile.read()
        assert content == "breh"
