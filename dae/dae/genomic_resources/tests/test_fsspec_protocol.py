import os
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
def dir_repo(tmp_path):
    """Build directory repository fixture."""

    demo_gtf_content = "TP53\tchr3\t300\t200"
    src_repo = GenomicResourceEmbededRepo("src", content={
        "one": {
            GR_CONF_FILE_NAME: "",
            "data.txt": "alabala"  # NOSONAR
        },
        "sub": {
            "two": {
                GR_CONF_FILE_NAME: ["type: gene_models\nfile: genes.gtf",
                                    '2021-11-20T00:00:56'],
                "genes.txt": demo_gtf_content
            }
        }
    })
    repo = GenomicResourceDirRepo('dir', directory=tmp_path)
    repo.store_all_resources(src_repo)
    repo.build_repo_content()

    return repo

@pytest.fixture
def fsspec_proto(dir_repo, s3):
    """Builds fsspec local filesystem protocol fixture."""

    assert os.path.exists(os.path.join(dir_repo.directory, ".CONTENTS"))

    def builder(filesystem="local"):
        if filesystem == "local":
            return FsspecReadWriteProtocol(
                "test", dir_repo.directory, LocalFileSystem())

        if filesystem == "s3":
            s3_path = "s3://test-bucket"
            for root, _, files in os.walk(dir_repo.directory):
                print(files)

                for fname in files:
                    root_rel = os.path.relpath(root, dir_repo.directory)
                    if root_rel == '.':
                        root_rel = ''
                    s3.put(
                        os.path.join(root, fname),
                        os.path.join(s3_path, root_rel, fname))

            return FsspecReadWriteProtocol("test", s3_path, s3)
        return None

    return builder


@pytest.mark.parametrize("filesystem", [
    "local",
    "s3",
])
def test_fsspec_proto_simple(fsspec_proto, filesystem):
    """Simple test for fsspec local filesystem proto"""
    proto = fsspec_proto(filesystem)
    resources = list(proto.collect_all_resources())
    assert len(resources) == 2


@pytest.mark.parametrize("filesystem", [
    "local",
    "s3",
])
def test_fsspec_proto_resource_paths(fsspec_proto, filesystem):
    """Tests resource paths."""
    proto = fsspec_proto(filesystem)

    res = proto.get_resource("one")

    res_path = proto.get_resource_path(res)
    assert os.path.relpath(res_path, proto.root_path) == "one"

    config_path = proto.get_resource_file_path(
        res, "genomic_resource.yaml")
    assert os.path.relpath(config_path, proto.root_path) == \
        "one/genomic_resource.yaml"


@pytest.mark.parametrize("filesystem", [
    "local",
    "s3",
])
def test_collect_resource_entries(fsspec_proto, filesystem):
    """Test collection of resource entries."""
    proto = fsspec_proto(filesystem)

    res = proto.get_resource("one")

    entries = proto.collect_resource_entries(res)
    assert len(entries) == 2

    entry = entries[0]
    assert entry.name == "data.txt"
    assert entry.size == 7

    entry = entries[1]
    assert entry.name == "genomic_resource.yaml"
    assert entry.size == 0


@pytest.mark.parametrize("filesystem", [
    "local",
    "s3",
])
def test_file_exists(fsspec_proto, filesystem):
    """Tests file_exists method."""
    proto = fsspec_proto(filesystem)

    res = proto.get_resource("one")

    assert proto.file_exists(res, "genomic_resource.yaml")
    assert not proto.file_exists(res, "alabala.txt")


@pytest.mark.parametrize("filesystem", [
    "local",
    "s3",
])
def test_open_raw_file_text_read(fsspec_proto, filesystem):
    """Test simple open with mode='rt'."""
    proto = fsspec_proto(filesystem)

    res = proto.get_resource("one")

    with proto.open_raw_file(res, "data.txt", mode="rt") as infile:
        content = infile.read()
        assert content == "alabala"

@pytest.mark.parametrize("filesystem", [
    "local",
    "s3",
])
def test_open_raw_file_text_write(fsspec_proto, filesystem):
    """Test simple open with mode='wt'."""
    proto = fsspec_proto(filesystem)

    res = proto.get_resource("one")

    with proto.open_raw_file(res, "new_data.txt", mode="wt") as infile:
        infile.write("new alabala")

    assert proto.file_exists(res, "new_data.txt")


@pytest.mark.parametrize("filesystem", [
    "local",
    "s3",
])
def test_open_raw_file_text_write_compression(fsspec_proto, filesystem):
    """Test open with mode='wt' and compression."""
    proto = fsspec_proto(filesystem)

    res = proto.get_resource("one")

    with proto.open_raw_file(
            res, "new_data.txt.gz", mode="wt", compression=True) as outfile:
        outfile.write("new alabala")

    assert proto.file_exists(res, "new_data.txt.gz")

    filepath = proto.get_resource_file_path(res, "new_data.txt.gz")
    with gzip.open(
            proto.filesystem.open(filepath), mode="rt") as infile:
        content = infile.read()
        assert content == "new alabala"


@pytest.mark.parametrize("filesystem", [
    "local",
    "s3",
])
def test_open_raw_file_text_read_compression(fsspec_proto, filesystem):
    """Test open with mode='rt' and compression."""
    proto = fsspec_proto(filesystem)

    res = proto.get_resource("one")

    filepath = proto.get_resource_file_path(res, "new_data.txt.gz")
    with proto.filesystem.open(
            filepath, mode="wt", compression="gzip") as outfile:
        outfile.write("new alabala")

    assert proto.file_exists(res, "new_data.txt.gz")

    with proto.open_raw_file(
            res, "new_data.txt.gz", mode="rt", compression=True) as infile:
        content = infile.read()
        assert content == "new alabala"


@pytest.mark.parametrize("filesystem", [
    "local",
    "s3",
])
def test_compute_md5_sum(fsspec_proto, filesystem):
    """Test md5 sum computation."""

    proto = fsspec_proto(filesystem)

    res = proto.get_resource("one")

    assert proto.compute_md5_sum(res, "data.txt") == \
         "c1cfdaf7e22865b29b8d62a564dc8f23"
    assert proto.compute_md5_sum(res, "genomic_resource.yaml") == \
         "d41d8cd98f00b204e9800998ecf8427e"


@pytest.mark.parametrize("filesystem", [
    "local",
    "s3",
])
def test_build_manifest(fsspec_proto, filesystem):
    """Test build manifest."""

    proto = fsspec_proto(filesystem)

    res = proto.get_resource("one")

    manifest = proto.build_manifest(res)

    assert len(manifest) == 2
    assert manifest["data.txt"].size == 7
    assert manifest["data.txt"].md5 == \
        "c1cfdaf7e22865b29b8d62a564dc8f23"

    assert manifest["genomic_resource.yaml"].size == 0
    assert manifest["genomic_resource.yaml"].md5 == \
        "d41d8cd98f00b204e9800998ecf8427e"


@pytest.mark.parametrize("filesystem", [
    "local",
    "s3",
])
def test_load_manifest(fsspec_proto, filesystem):
    """Test load manifest."""

    proto = fsspec_proto(filesystem)

    res = proto.get_resource("one")

    manifest = proto.load_manifest(res)

    assert len(manifest) == 2

    assert len(manifest) == 2
    assert manifest["data.txt"].size == 7
    assert manifest["data.txt"].md5 == \
        "c1cfdaf7e22865b29b8d62a564dc8f23"

    assert manifest["genomic_resource.yaml"].size == 0
    assert manifest["genomic_resource.yaml"].md5 == \
        "d41d8cd98f00b204e9800998ecf8427e"


@pytest.mark.parametrize("filesystem", [
    "local",
    "s3",
])
def test_load_missing_manifest(fsspec_proto, filesystem):
    """Test load missing manifest."""

    proto = fsspec_proto(filesystem)

    res = proto.get_resource("one")

    manifest_filename = proto.get_resource_file_path(res, ".MANIFEST")
    assert proto.filesystem.exists(manifest_filename)

    proto.filesystem.delete(manifest_filename)
    assert not proto.filesystem.exists(manifest_filename)

    with pytest.raises(FileNotFoundError):
        proto.load_manifest(res)


@pytest.mark.parametrize("filesystem", [
    "local",
    "s3",
])
def test_get_manifest(fsspec_proto, filesystem):
    """Test get manifest."""

    proto = fsspec_proto(filesystem)

    res = proto.get_resource("one")

    manifest = proto.get_manifest(res)

    assert len(manifest) == 2

    assert len(manifest) == 2
    assert manifest["data.txt"].size == 7
    assert manifest["data.txt"].md5 == \
        "c1cfdaf7e22865b29b8d62a564dc8f23"

    assert manifest["genomic_resource.yaml"].size == 0
    assert manifest["genomic_resource.yaml"].md5 == \
        "d41d8cd98f00b204e9800998ecf8427e"


@pytest.mark.parametrize("filesystem", [
    "local",
    "s3",
])
def test_get_missing_manifest(fsspec_proto, filesystem):
    """Test get missing manifest. The manifest should be recreated."""

    proto = fsspec_proto(filesystem)

    res = proto.get_resource("one")

    manifest_filename = proto.get_resource_file_path(res, ".MANIFEST")
    assert proto.filesystem.exists(manifest_filename)

    proto.filesystem.delete(manifest_filename)
    assert not proto.filesystem.exists(manifest_filename)

    # now manifest file is missing... proto should recreate it...
    manifest = proto.get_manifest(res)

    assert len(manifest) == 2

    assert len(manifest) == 2
    assert manifest["data.txt"].size == 7
    assert manifest["data.txt"].md5 == \
        "c1cfdaf7e22865b29b8d62a564dc8f23"

    assert manifest["genomic_resource.yaml"].size == 0
    assert manifest["genomic_resource.yaml"].md5 == \
        "d41d8cd98f00b204e9800998ecf8427e"


@pytest.mark.parametrize("filesystem", [
    "local",
    "s3",
])
def test_delete_manifest_entry(fsspec_proto, filesystem):
    """Test delete manifest entry."""

    # Given
    proto = fsspec_proto(filesystem)

    res = proto.get_resource("one")

    manifest = proto.load_manifest(res)

    entry = manifest["data.txt"]
    entry_filename = proto.get_resource_file_path(res, entry.name)
    assert proto.filesystem.exists(entry_filename)

    # When
    proto._delete_manifest_entry(res, entry)  # pylint: disable=protected-access

    # Then
    assert not proto.filesystem.exists(entry_filename)


@pytest.mark.parametrize("filesystem", [
    "local",
    "s3",
])
def test_copy_manifest_entry(dir_repo, fsspec_proto, filesystem):
    """Test delete manifest entry."""

    # Given
    remote_res = dir_repo.get_resource("one")
    assert remote_res is not None
    assert remote_res.file_exists("data.txt")

    proto = fsspec_proto(filesystem)

    res = proto.get_resource("one")

    manifest = proto.load_manifest(res)

    entry = manifest["data.txt"]
    entry_filename = proto.get_resource_file_path(res, entry.name)
    assert proto.filesystem.exists(entry_filename)
