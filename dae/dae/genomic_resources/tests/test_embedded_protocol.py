# pylint: disable=redefined-outer-name,C0114,C0116,protected-access

import pytest

from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.embedded_protocol import \
    EmbeddedProtocol


@pytest.fixture
def emb_proto():
    """Build directory repository fixture."""
    demo_gtf_content = "TP53\tchr3\t300\t200"
    proto = EmbeddedProtocol("src", content={
        "one": {
            GR_CONF_FILE_NAME: "",
            "data.txt": "alabala"
        },
        "sub": {
            "two(1.0)": {
                GR_CONF_FILE_NAME: "type: gene_models\nfile: genes.gtf",
                "genes.gtf": [
                    demo_gtf_content,
                    "2021-11-20T00:00:56+00:00"
                ]
            }
        }
    })

    return proto


def test_scan_resource_file_content_and_time(emb_proto):

    res = emb_proto._scan_resource_file_content_and_time(
        "one", (0,), "data.txt")

    assert res is not None
    assert res[0] == b"alabala"

    res = emb_proto._scan_resource_file_content_and_time(
        "sub/two", (1, 0), "genes.gtf")

    assert res is not None
    assert res[0] == b"TP53\tchr3\t300\t200"
    assert res[1] == "2021-11-20T00:00:56+00:00"


def test_embedded_proto_simple(emb_proto):
    resources = list(emb_proto.get_all_resources())
    assert len(resources) == 2


def test_get_resource(emb_proto):

    res = emb_proto.get_resource("sub/two")
    assert res.resource_id == "sub/two"
    assert res.version == (1, 0)


def test_load_manifest(emb_proto):

    res = emb_proto.get_resource("sub/two")
    manifest = emb_proto.load_manifest(res)

    entry = manifest["genes.gtf"]
    assert entry.name == "genes.gtf"
    assert entry.size == 17
    assert entry.time == "2021-11-20T00:00:56+00:00"
    assert entry.md5 == "d9636a8dca9e5626851471d1c0ea92b1"


def test_get_manifest(emb_proto):

    res = emb_proto.get_resource("sub/two")
    manifest = emb_proto.get_manifest(res)

    entry = manifest["genes.gtf"]
    assert entry.name == "genes.gtf"
    assert entry.size == 17
    assert entry.time == "2021-11-20T00:00:56+00:00"
    assert entry.md5 == "d9636a8dca9e5626851471d1c0ea92b1"
