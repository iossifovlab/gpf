# pylint: disable=redefined-outer-name,C0114,C0116,protected-access

import gzip
import pytest


@pytest.mark.parametrize("filesystem", [
    "file",
    "s3",
    "http"
])
def test_get_all_resources(fsspec_proto, filesystem):
    proto = fsspec_proto(filesystem)

    resources = list(proto.get_all_resources())
    assert len(resources) == 4, resources


@pytest.mark.parametrize("filesystem", [
    "file",
    "s3",
])
def test_collect_all_resources(fsspec_proto, filesystem):
    proto = fsspec_proto(filesystem)

    resources = list(proto.collect_all_resources())
    assert len(resources) == 4, resources


@pytest.mark.parametrize("filesystem", [
    "file",
    "s3",
])
def test_state_directory_exists(fsspec_proto, filesystem):
    proto = fsspec_proto(filesystem)

    assert proto.state_url.endswith(".grr")
    assert proto.filesystem.exists(proto.state_url)
    assert proto.filesystem.isdir(proto.state_url)


@pytest.mark.parametrize("filesystem", [
    "file",
    "s3",
])
def test_resource_paths(fsspec_proto, filesystem):
    proto = fsspec_proto(filesystem)

    res = proto.get_resource("one")

    res_path = proto.get_resource_url(res)
    assert res_path.endswith("one")

    config_path = proto.get_resource_file_url(
        res, "genomic_resource.yaml")
    assert config_path.endswith("one/genomic_resource.yaml")


@pytest.mark.parametrize("filesystem", [
    "file",
    "s3",
])
def test_build_resource_file_state(fsspec_proto, filesystem):
    proto = fsspec_proto(filesystem)
    timestamp = "2022-05-31T00:00:00+00:00"
    res = proto.get_resource("one")
    state = proto.build_resource_file_state(
        res, "data.txt", timestamp=timestamp)

    assert state.resource_id == "one"
    assert state.version == "0"
    assert state.filename == "data.txt"
    assert state.timestamp == timestamp
    assert state.md5 == "c1cfdaf7e22865b29b8d62a564dc8f23"

    res = proto.get_resource("sub/two")
    state = proto.build_resource_file_state(
        res, "genes.gtf", timestamp=timestamp)

    assert state.resource_id == "sub/two"
    assert state.version == "1.0"
    assert state.filename == "genes.gtf"
    assert state.timestamp == timestamp
    assert state.md5 == "d9636a8dca9e5626851471d1c0ea92b1"


@pytest.mark.parametrize("filesystem", [
    "file",
    "s3",
])
def test_save_load_resource_file_state(fsspec_proto, filesystem):
    proto = fsspec_proto(filesystem)
    timestamp = "2022-05-31T00:00:00+00:00"

    res = proto.get_resource("sub/two")
    state = proto.build_resource_file_state(
        res, "genes.gtf", timestamp=timestamp)

    proto.save_resource_file_state(state)
    state_path = proto._get_resource_file_state_path(res, "genes.gtf")
    assert proto.filesystem.exists(state_path)

    loaded = proto.load_resource_file_state(res, "genes.gtf")
    assert loaded is not None
    assert loaded.resource_id == "sub/two"
    assert loaded.version == "1.0"
    assert loaded.filename == "genes.gtf"
    assert loaded.timestamp == timestamp
    assert loaded.md5 == "d9636a8dca9e5626851471d1c0ea92b1"


@pytest.mark.parametrize("filesystem", [
    "file",
    "s3",
])
def test_collect_resource_entries(fsspec_proto, filesystem):
    proto = fsspec_proto(filesystem)

    res = proto.get_resource("one")

    entries = proto.collect_resource_entries(res)
    assert len(entries) == 4

    entry = entries["data.txt"]
    assert entry.name == "data.txt"
    assert entry.size == 7

    entry = entries["genomic_resource.yaml"]
    assert entry.name == "genomic_resource.yaml"
    assert entry.size == 0


@pytest.mark.parametrize("filesystem", [
    "file",
    "s3",
])
def test_file_exists(fsspec_proto, filesystem):
    proto = fsspec_proto(filesystem)

    res = proto.get_resource("one")

    assert proto.file_exists(res, "genomic_resource.yaml")
    assert not proto.file_exists(res, "alabala.txt")


@pytest.mark.parametrize("filesystem", [
    "file",
    "s3",
])
def test_open_raw_file_text_read(fsspec_proto, filesystem):
    proto = fsspec_proto(filesystem)

    res = proto.get_resource("one")

    with proto.open_raw_file(res, "data.txt", mode="rt") as infile:
        content = infile.read()
        assert content == "alabala"


@pytest.mark.parametrize("filesystem", [
    "file",
    "s3",
])
def test_open_raw_file_text_write(fsspec_proto, filesystem):
    proto = fsspec_proto(filesystem)

    res = proto.get_resource("one")

    with proto.open_raw_file(res, "new_data.txt", mode="wt") as infile:
        infile.write("new alabala")

    assert proto.file_exists(res, "new_data.txt")


@pytest.mark.parametrize("filesystem", [
    "file",
    "s3",
])
def test_open_raw_file_text_write_compression(fsspec_proto, filesystem):
    proto = fsspec_proto(filesystem)

    res = proto.get_resource("one")

    with proto.open_raw_file(
            res, "new_data.txt.gz", mode="wt", compression=True) as outfile:
        outfile.write("new alabala")

    assert proto.file_exists(res, "new_data.txt.gz")

    filepath = proto.get_resource_file_url(res, "new_data.txt.gz")
    with gzip.open(
            proto.filesystem.open(filepath), mode="rt") as infile:
        content = infile.read()
        assert content == "new alabala"


@pytest.mark.parametrize("filesystem", [
    "file",
    "s3",
])
def test_open_raw_file_text_read_compression(fsspec_proto, filesystem):
    proto = fsspec_proto(filesystem)

    res = proto.get_resource("one")

    filepath = proto.get_resource_file_url(res, "new_data.txt.gz")
    with proto.filesystem.open(
            filepath, mode="wt", compression="gzip") as outfile:
        outfile.write("new alabala")

    assert proto.file_exists(res, "new_data.txt.gz")

    with proto.open_raw_file(
            res, "new_data.txt.gz", mode="rt", compression=True) as infile:
        content = infile.read()
        assert content == "new alabala"


@pytest.mark.parametrize("filesystem", [
    "file",
    "s3",
])
def test_compute_md5_sum(fsspec_proto, filesystem):
    proto = fsspec_proto(filesystem)

    res = proto.get_resource("one")

    assert proto.compute_md5_sum(res, "data.txt") == \
        "c1cfdaf7e22865b29b8d62a564dc8f23"
    assert proto.compute_md5_sum(res, "genomic_resource.yaml") == \
        "d41d8cd98f00b204e9800998ecf8427e"


@pytest.mark.parametrize("filesystem", [
    "file",
    "s3",
])
def test_build_manifest(fsspec_proto, filesystem):
    proto = fsspec_proto(filesystem)

    res = proto.get_resource("one")

    manifest = proto.build_manifest(res)

    assert len(manifest) == 4
    assert manifest["data.txt"].size == 7
    assert manifest["data.txt"].md5 == \
        "c1cfdaf7e22865b29b8d62a564dc8f23"

    assert manifest["genomic_resource.yaml"].size == 0
    assert manifest["genomic_resource.yaml"].md5 == \
        "d41d8cd98f00b204e9800998ecf8427e"


@pytest.mark.parametrize("filesystem", [
    "file",
    "s3",
])
def test_load_manifest(fsspec_proto, filesystem):
    proto = fsspec_proto(filesystem)

    res = proto.get_resource("one")

    manifest = proto.load_manifest(res)

    assert len(manifest) == 4
    assert manifest["data.txt"].size == 7
    assert manifest["data.txt"].md5 == \
        "c1cfdaf7e22865b29b8d62a564dc8f23"

    assert manifest["genomic_resource.yaml"].size == 0
    assert manifest["genomic_resource.yaml"].md5 == \
        "d41d8cd98f00b204e9800998ecf8427e"


@pytest.mark.parametrize("filesystem", [
    "file",
    "s3",
])
def test_load_missing_manifest(fsspec_proto, filesystem):
    proto = fsspec_proto(filesystem)

    res = proto.get_resource("one")

    manifest_filename = proto.get_resource_file_url(res, ".MANIFEST")
    assert proto.filesystem.exists(manifest_filename)

    proto.filesystem.delete(manifest_filename)
    assert not proto.filesystem.exists(manifest_filename)

    with pytest.raises(FileNotFoundError):
        proto.load_manifest(res)


@pytest.mark.parametrize("filesystem", [
    "file",
    "s3",
])
def test_get_manifest(fsspec_proto, filesystem):
    proto = fsspec_proto(filesystem)

    res = proto.get_resource("one")

    manifest = proto.get_manifest(res)

    assert len(manifest) == 4

    assert manifest["data.txt"].size == 7
    assert manifest["data.txt"].md5 == \
        "c1cfdaf7e22865b29b8d62a564dc8f23"

    assert manifest["genomic_resource.yaml"].size == 0
    assert manifest["genomic_resource.yaml"].md5 == \
        "d41d8cd98f00b204e9800998ecf8427e"


@pytest.mark.parametrize("filesystem", [
    "file",
    "s3",
])
def test_get_missing_manifest(fsspec_proto, filesystem):
    proto = fsspec_proto(filesystem)

    res = proto.get_resource("one")

    manifest_filename = proto.get_resource_file_url(res, ".MANIFEST")
    assert proto.filesystem.exists(manifest_filename)

    proto.filesystem.delete(manifest_filename)
    assert not proto.filesystem.exists(manifest_filename)

    # now manifest file is missing... proto should recreate it...
    manifest = proto.get_manifest(res)

    assert len(manifest) == 4
    assert manifest["data.txt"].size == 7
    assert manifest["data.txt"].md5 == \
        "c1cfdaf7e22865b29b8d62a564dc8f23"

    assert manifest["genomic_resource.yaml"].size == 0
    assert manifest["genomic_resource.yaml"].md5 == \
        "d41d8cd98f00b204e9800998ecf8427e"


@pytest.mark.parametrize("filesystem", [
    "file",
    "s3",
])
def test_delete_resource_file(fsspec_proto, filesystem):

    # Given
    proto = fsspec_proto(filesystem)

    res = proto.get_resource("sub/two")

    path = proto.get_resource_file_url(res, "genes.gtf")
    assert proto.filesystem.exists(path)

    # When
    proto.delete_resource_file(res, "genes.gtf")

    # Then
    assert not proto.filesystem.exists(path)


@pytest.mark.parametrize("filesystem", [
    "file",
    "s3",
])
def test_copy_resource_file(embedded_proto, fsspec_proto, filesystem):
    # Given
    src_proto = embedded_proto()
    proto = fsspec_proto(filesystem)

    src_res = src_proto.get_resource("sub/two")
    dst_res = proto.get_resource("sub/two")

    # When
    state = proto.copy_resource_file(src_res, dst_res, "genes.gtf")

    # Then
    timestamp = proto.get_resource_file_timestamp(dst_res, "genes.gtf")

    assert state.resource_id == "sub/two"
    assert state.version == "1.0"
    assert state.filename == "genes.gtf"
    assert state.timestamp == timestamp
    assert state.md5 == "d9636a8dca9e5626851471d1c0ea92b1"

    loaded = proto.load_resource_file_state(dst_res, "genes.gtf")
    assert loaded == state


@pytest.mark.parametrize("filesystem", [
    "file",
    "s3",
])
def test_copy_resource(embedded_proto, fsspec_proto, filesystem):

    # Given
    src_proto = embedded_proto()
    proto = fsspec_proto(filesystem)

    src_res = src_proto.get_resource("sub/two")

    # When
    proto.copy_resource(src_res)

    # Then
    dst_res = proto.get_resource("sub/two")
    timestamp = proto.get_resource_file_timestamp(dst_res, "genes.gtf")

    state = proto.load_resource_file_state(dst_res, "genes.gtf")

    assert state.resource_id == "sub/two"
    assert state.version == "1.0"
    assert state.filename == "genes.gtf"
    assert state.timestamp == timestamp
    assert state.md5 == "d9636a8dca9e5626851471d1c0ea92b1"


@pytest.mark.parametrize("filesystem", [
    "file",
    "s3",
])
def test_update_resource_file_when_missing(
        embedded_proto, fsspec_proto, filesystem):

    # Given
    src_proto = embedded_proto()
    proto = fsspec_proto(filesystem)

    src_res = src_proto.get_resource("sub/two")
    dst_res = proto.get_resource("sub/two")

    proto.delete_resource_file(dst_res, "genes.gtf")
    assert not proto.file_exists(dst_res, "genes.gtf")

    # When
    state = proto.update_resource_file(src_res, dst_res, "genes.gtf")

    # Then
    assert proto.file_exists(dst_res, "genes.gtf")

    timestamp = proto.get_resource_file_timestamp(dst_res, "genes.gtf")

    assert state.resource_id == "sub/two"
    assert state.version == "1.0"
    assert state.filename == "genes.gtf"
    assert state.timestamp == timestamp
    assert state.md5 == "d9636a8dca9e5626851471d1c0ea92b1"


@pytest.mark.parametrize("filesystem", [
    "file",
    "s3",
])
def test_update_resource_file_when_changed(
        embedded_proto, fsspec_proto, filesystem):

    # Given
    src_proto = embedded_proto()
    proto = fsspec_proto(filesystem)

    src_res = src_proto.get_resource("sub/two")
    dst_res = proto.get_resource("sub/two")

    with proto.open_raw_file(dst_res, "genes.gtf", mode="wt") as outfile:
        outfile.write("aaaa")
    proto.save_manifest(dst_res, proto.build_manifest(dst_res))

    # When
    state = proto.update_resource_file(src_res, dst_res, "genes.gtf")

    # Then
    assert proto.file_exists(dst_res, "genes.gtf")

    timestamp = proto.get_resource_file_timestamp(dst_res, "genes.gtf")

    assert state.resource_id == "sub/two"
    assert state.version == "1.0"
    assert state.filename == "genes.gtf"
    assert state.timestamp == timestamp
    assert state.md5 == "d9636a8dca9e5626851471d1c0ea92b1"
