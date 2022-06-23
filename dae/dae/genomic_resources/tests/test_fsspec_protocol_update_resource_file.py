# pylint: disable=W0621,C0114,C0116,W0212,W0613

import time
import pytest


@pytest.mark.parametrize("scheme", [
    "file",
    "s3",
])
def test_update_resource_file_when_file_missing(
        embedded_proto, fsspec_proto, scheme):

    # Given
    src_proto = embedded_proto()
    proto = fsspec_proto(scheme)

    src_res = src_proto.get_resource("sub/two")
    dst_res = proto.get_resource("sub/two")

    proto.filesystem.delete(
        proto.get_resource_file_url(dst_res, "genes.gtf"))

    assert not proto.file_exists(dst_res, "genes.gtf")
    assert proto.load_resource_file_state(dst_res, "genes.gtf")

    # When
    state = proto.update_resource_file(src_res, dst_res, "genes.gtf")

    # Then
    assert proto.file_exists(dst_res, "genes.gtf")

    timestamp = proto.get_resource_file_timestamp(dst_res, "genes.gtf")

    assert state.filename == "genes.gtf"
    assert state.timestamp == timestamp
    assert state.timestamp == pytest.approx(time.time(), abs=5)
    assert state.md5 == "d9636a8dca9e5626851471d1c0ea92b1"


@pytest.mark.parametrize("scheme", [
    "file",
    "s3",
])
def test_update_resource_file_when_state_missing(
        embedded_proto, fsspec_proto, scheme):

    # Given
    src_proto = embedded_proto()
    proto = fsspec_proto(scheme)

    src_res = src_proto.get_resource("sub/two")
    dst_res = proto.get_resource("sub/two")

    proto.filesystem.delete(
        proto._get_resource_file_state_path(dst_res, "genes.gtf"))

    assert proto.file_exists(dst_res, "genes.gtf")
    assert not proto.load_resource_file_state(dst_res, "genes.gtf")
    fileurl = proto.get_resource_file_url(dst_res, "genes.gtf")
    timestamp = proto.filesystem.modified(fileurl)

    # When
    state = proto.update_resource_file(src_res, dst_res, "genes.gtf")

    # Then
    assert proto.file_exists(dst_res, "genes.gtf")

    assert state.filename == "genes.gtf"
    assert state.md5 == "d9636a8dca9e5626851471d1c0ea92b1"
    assert proto.filesystem.modified(fileurl) == timestamp


@pytest.mark.parametrize("scheme", [
    "file",
    "s3",
])
def test_update_resource_file_when_changed(
        embedded_proto, fsspec_proto, scheme):

    # Given
    src_proto = embedded_proto()
    proto = fsspec_proto(scheme)

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

    assert state.filename == "genes.gtf"
    assert state.timestamp == timestamp
    assert state.timestamp == pytest.approx(time.time(), abs=5)

    assert state.md5 == "d9636a8dca9e5626851471d1c0ea92b1"


@pytest.mark.parametrize("scheme", [
    "file",
    "s3",
])
def test_do_not_update_resource_file_when_state_changed_but_file_not(
        embedded_proto, fsspec_proto, scheme):

    # Given
    src_proto = embedded_proto()
    proto = fsspec_proto(scheme)

    src_res = src_proto.get_resource("sub/two")
    dst_res = proto.get_resource("sub/two")

    state = proto.load_resource_file_state(dst_res, "genes.gtf")
    state.timestamp = 0

    proto.save_resource_file_state(dst_res, state)

    fileurl = proto.get_resource_file_url(dst_res, "genes.gtf")
    fileid = (
        proto.filesystem.modified(fileurl),)

    # When
    proto.update_resource_file(src_res, dst_res, "genes.gtf")

    # Then: file not changed
    assert fileid == (
        proto.filesystem.modified(fileurl), )
