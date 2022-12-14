# pylint: disable=W0621,C0114,C0116,W0212,W0613

import gzip
import time
import pytest

from dae.genomic_resources.testing import \
    build_inmemory_test_protocol


def test_collect_all_resources(rw_fsspec_proto):
    proto = rw_fsspec_proto

    resources = list(proto.collect_all_resources())
    assert len(resources) == 5, resources


def test_resource_paths(rw_fsspec_proto):
    proto = rw_fsspec_proto

    res = proto.get_resource("one")

    res_path = proto.get_resource_url(res)
    assert res_path.endswith("one")

    config_path = proto.get_resource_file_url(
        res, "genomic_resource.yaml")
    assert config_path.endswith("one/genomic_resource.yaml")


def test_build_resource_file_state(rw_fsspec_proto):
    proto = rw_fsspec_proto
    timestamp = time.time()
    res = proto.get_resource("one")

    state = proto.build_resource_file_state(
        res, "data.txt")

    assert state.filename == "data.txt"
    assert state.timestamp == pytest.approx(timestamp, abs=5)
    assert state.md5 == "c1cfdaf7e22865b29b8d62a564dc8f23"

    res = proto.get_resource("sub/two")
    state = proto.build_resource_file_state(
        res, "genes.gtf")

    assert state.filename == "genes.gtf"
    assert state.timestamp == pytest.approx(timestamp, abs=5)
    assert state.md5 == "d9636a8dca9e5626851471d1c0ea92b1"


def test_save_load_resource_file_state(rw_fsspec_proto):
    proto = rw_fsspec_proto
    timestamp = time.time()

    res = proto.get_resource("sub/two")
    state = proto.build_resource_file_state(
        res, "genes.gtf")

    proto.save_resource_file_state(res, state)
    state_path = proto._get_resource_file_state_path(res, "genes.gtf")
    assert proto.filesystem.exists(state_path)

    loaded = proto.load_resource_file_state(res, "genes.gtf")
    assert loaded is not None
    assert loaded.filename == "genes.gtf"
    assert loaded.timestamp == pytest.approx(timestamp, abs=5)
    assert loaded.md5 == "d9636a8dca9e5626851471d1c0ea92b1"


def test_collect_resource_entries(rw_fsspec_proto):
    proto = rw_fsspec_proto

    res = proto.get_resource("one")

    entries = proto.collect_resource_entries(res)
    assert len(entries) == 2

    entry = entries["data.txt"]
    assert entry.name == "data.txt"
    assert entry.size == 7

    entry = entries["genomic_resource.yaml"]
    assert entry.name == "genomic_resource.yaml"
    assert entry.size == 0


def test_file_exists(rw_fsspec_proto):
    proto = rw_fsspec_proto

    res = proto.get_resource("one")

    assert proto.file_exists(res, "genomic_resource.yaml")
    assert not proto.file_exists(res, "alabala.txt")


def test_open_raw_file_text_read(rw_fsspec_proto):
    proto = rw_fsspec_proto

    res = proto.get_resource("one")

    with proto.open_raw_file(res, "data.txt", mode="rt") as infile:
        content = infile.read()
        assert content == "alabala"


def test_open_raw_file_text_write(rw_fsspec_proto):
    proto = rw_fsspec_proto

    res = proto.get_resource("one")

    with proto.open_raw_file(res, "new_data.txt", mode="wt") as infile:
        infile.write("new alabala")

    assert proto.file_exists(res, "new_data.txt")


def test_open_raw_file_text_write_compression(rw_fsspec_proto):
    proto = rw_fsspec_proto

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


def test_open_raw_file_text_read_compression(rw_fsspec_proto):
    proto = rw_fsspec_proto

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


def test_compute_md5_sum(rw_fsspec_proto):
    proto = rw_fsspec_proto

    res = proto.get_resource("one")

    assert proto.compute_md5_sum(res, "data.txt") == \
        "c1cfdaf7e22865b29b8d62a564dc8f23"
    assert proto.compute_md5_sum(res, "genomic_resource.yaml") == \
        "d41d8cd98f00b204e9800998ecf8427e"


def test_build_manifest(rw_fsspec_proto):
    proto = rw_fsspec_proto

    res = proto.get_resource("one")

    manifest = proto.build_manifest(res)

    assert len(manifest) == 2
    assert manifest["data.txt"].size == 7
    assert manifest["data.txt"].md5 == \
        "c1cfdaf7e22865b29b8d62a564dc8f23"

    assert manifest["genomic_resource.yaml"].size == 0
    assert manifest["genomic_resource.yaml"].md5 == \
        "d41d8cd98f00b204e9800998ecf8427e"


def test_load_manifest(rw_fsspec_proto):
    proto = rw_fsspec_proto

    res = proto.get_resource("one")

    manifest = proto.load_manifest(res)

    assert len(manifest) == 2
    assert manifest["data.txt"].size == 7
    assert manifest["data.txt"].md5 == \
        "c1cfdaf7e22865b29b8d62a564dc8f23"

    assert manifest["genomic_resource.yaml"].size == 0
    assert manifest["genomic_resource.yaml"].md5 == \
        "d41d8cd98f00b204e9800998ecf8427e"


def test_load_missing_manifest(rw_fsspec_proto):
    proto = rw_fsspec_proto

    res = proto.get_resource("one")

    manifest_filename = proto.get_resource_file_url(res, ".MANIFEST")
    assert proto.filesystem.exists(manifest_filename)

    proto.filesystem.delete(manifest_filename)
    assert not proto.filesystem.exists(manifest_filename)

    with pytest.raises(FileNotFoundError):
        proto.load_manifest(res)


def test_get_manifest(rw_fsspec_proto):
    proto = rw_fsspec_proto

    res = proto.get_resource("one")

    manifest = proto.get_manifest(res)

    assert len(manifest) == 2

    assert manifest["data.txt"].size == 7
    assert manifest["data.txt"].md5 == \
        "c1cfdaf7e22865b29b8d62a564dc8f23"

    assert manifest["genomic_resource.yaml"].size == 0
    assert manifest["genomic_resource.yaml"].md5 == \
        "d41d8cd98f00b204e9800998ecf8427e"


def test_get_missing_manifest(rw_fsspec_proto):
    proto = rw_fsspec_proto

    res = proto.get_resource("one")

    manifest_filename = proto.get_resource_file_url(res, ".MANIFEST")
    assert proto.filesystem.exists(manifest_filename)

    proto.filesystem.delete(manifest_filename)
    assert not proto.filesystem.exists(manifest_filename)

    # now manifest file is missing... proto should recreate it...
    manifest = proto.get_manifest(res)

    assert len(manifest) == 2
    assert manifest["data.txt"].size == 7
    assert manifest["data.txt"].md5 == \
        "c1cfdaf7e22865b29b8d62a564dc8f23"

    assert manifest["genomic_resource.yaml"].size == 0
    assert manifest["genomic_resource.yaml"].md5 == \
        "d41d8cd98f00b204e9800998ecf8427e"


def test_delete_resource_file(rw_fsspec_proto):

    # Given
    proto = rw_fsspec_proto

    res = proto.get_resource("sub/two")

    path = proto.get_resource_file_url(res, "genes.gtf")
    assert proto.filesystem.exists(path)

    # When
    proto.delete_resource_file(res, "genes.gtf")

    # Then
    assert not proto.filesystem.exists(path)


def test_copy_resource_file(content_fixture, rw_fsspec_proto):
    # Given
    src_proto = build_inmemory_test_protocol(content_fixture)
    proto = rw_fsspec_proto

    src_res = src_proto.get_resource("sub/two")
    dst_res = proto.get_resource("sub/two")

    # When
    state = proto.copy_resource_file(src_res, dst_res, "genes.gtf")

    # Then
    timestamp = proto.get_resource_file_timestamp(dst_res, "genes.gtf")

    assert state.filename == "genes.gtf"
    assert state.timestamp == timestamp
    assert state.md5 == "d9636a8dca9e5626851471d1c0ea92b1"

    loaded = proto.load_resource_file_state(dst_res, "genes.gtf")
    assert loaded == state


def test_copy_resource(content_fixture, rw_fsspec_proto):

    # Given
    src_proto = build_inmemory_test_protocol(content_fixture)
    proto = rw_fsspec_proto

    src_res = src_proto.get_resource("sub/two")

    # When
    proto.copy_resource(src_res)

    # Then
    dst_res = proto.get_resource("sub/two")
    timestamp = proto.get_resource_file_timestamp(dst_res, "genes.gtf")

    state = proto.load_resource_file_state(dst_res, "genes.gtf")

    assert state.filename == "genes.gtf"
    assert state.timestamp == timestamp
    assert state.timestamp == pytest.approx(time.time(), abs=5)
    assert state.md5 == "d9636a8dca9e5626851471d1c0ea92b1"
