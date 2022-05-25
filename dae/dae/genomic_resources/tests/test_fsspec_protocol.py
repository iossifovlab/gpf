import gzip
import pytest

from fsspec.implementations.local import LocalFileSystem  # type: ignore

from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.embeded_repository import \
    GenomicResourceEmbededRepo
from dae.genomic_resources.dir_repository import GenomicResourceDirRepo
from dae.genomic_resources.fsspec_protocol import FsspecReadWriteProtocol

# pylint: disable=redefined-outer-name

@pytest.fixture
def fsspec_proto(tmp_path):
    """Builds fsspec local filesystem protocol fixture."""
    demo_gtf_content = "TP53\tchr3\t300\t200"
    src_repo = GenomicResourceEmbededRepo("src", content={
        "one": {
            GR_CONF_FILE_NAME: "",
            "data.txt": "alabala"  # NOSONAR
        },
        "sub": {
            "two[1.0]": {
                GR_CONF_FILE_NAME: ["type: gene_models\nfile: genes.gtf",
                                    '2021-11-20T00:00:56'],
                "genes.txt": demo_gtf_content
            }
        }
    })
    dir_repo = GenomicResourceDirRepo('dir', directory=tmp_path)
    dir_repo.store_all_resources(src_repo)

    return FsspecReadWriteProtocol("test", tmp_path, LocalFileSystem())


def test_fsspec_proto_simple(fsspec_proto):
    """Simple test for fsspec local filesystem proto"""
    resources = list(fsspec_proto.collect_all_resources())
    assert len(resources) == 2


def test_fsspec_proto_resource_paths(fsspec_proto):
    """Tests resource paths."""

    res = list(fsspec_proto.collect_all_resources())[0]

    res_path = fsspec_proto.get_resource_path(res)
    assert res_path.relative_to(fsspec_proto.root_url).name == "one"

    config_path = fsspec_proto.get_resource_file_path(
        res, "genomic_resource.yaml")
    assert config_path.relative_to(fsspec_proto.root_url).name == \
        "genomic_resource.yaml"


def test_collect_resource_entries(fsspec_proto):
    """Test collection of resource entries."""

    res = list(fsspec_proto.collect_all_resources())[0]
    assert res.resource_id == "one"

    entries = fsspec_proto.collect_resource_entries(res)
    assert len(entries) == 2

    entry = entries[0]
    assert entry.name == "data.txt"
    assert entry.size == 7

    entry = entries[1]
    assert entry.name == "genomic_resource.yaml"
    assert entry.size == 0


def test_file_exists(fsspec_proto):
    """Tests file_exists method."""

    res = list(fsspec_proto.collect_all_resources())[0]
    assert res.resource_id == "one"

    assert fsspec_proto.file_exists(res, "genomic_resource.yaml")
    assert not fsspec_proto.file_exists(res, "alabala.txt")


def test_open_raw_file_text_read(fsspec_proto):
    """Test simple open with mode='rt'."""

    res = list(fsspec_proto.collect_all_resources())[0]
    assert res.resource_id == "one"

    with fsspec_proto.open_raw_file(res, "data.txt", mode="rt") as infile:
        content = infile.read()
        assert content == "alabala"

def test_open_raw_file_text_write(fsspec_proto):
    """Test simple open with mode='wt'."""

    res = list(fsspec_proto.collect_all_resources())[0]
    assert res.resource_id == "one"

    with fsspec_proto.open_raw_file(res, "new_data.txt", mode="wt") as infile:
        infile.write("new alabala")

    assert fsspec_proto.file_exists(res, "new_data.txt")


def test_open_raw_file_text_write_compression(fsspec_proto):
    """Test open with mode='wt' and compression."""

    res = list(fsspec_proto.collect_all_resources())[0]
    assert res.resource_id == "one"

    with fsspec_proto.open_raw_file(
            res, "new_data.txt.gz", mode="wt", compression=True) as outfile:
        outfile.write("new alabala")

    assert fsspec_proto.file_exists(res, "new_data.txt.gz")

    filepath = fsspec_proto.get_resource_file_path(res, "new_data.txt.gz")
    with gzip.open(filepath, mode="rt") as infile:
        content = infile.read()
        assert content == "new alabala"


def test_open_raw_file_text_read_compression(fsspec_proto):
    """Test open with mode='rt' and compression."""

    res = list(fsspec_proto.collect_all_resources())[0]
    assert res.resource_id == "one"

    filepath = fsspec_proto.get_resource_file_path(res, "new_data.txt.gz")
    with gzip.open(filepath, mode="wt") as outfile:
        outfile.write("new alabala")

    assert fsspec_proto.file_exists(res, "new_data.txt.gz")

    with fsspec_proto.open_raw_file(
            res, "new_data.txt.gz", mode="rt", compression=True) as infile:
        content = infile.read()
        assert content == "new alabala"
