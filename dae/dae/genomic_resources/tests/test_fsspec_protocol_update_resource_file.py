# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import Any

import time
import pytest

from dae.genomic_resources.testing import \
    build_inmemory_test_protocol
from dae.genomic_resources.fsspec_protocol import FsspecReadWriteProtocol


def test_update_resource_file_when_file_missing(
        content_fixture: dict[str, Any],
        rw_fsspec_proto: FsspecReadWriteProtocol) -> None:

    # Given
    src_proto = build_inmemory_test_protocol(content_fixture)
    proto = rw_fsspec_proto

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

    assert state is not None
    assert state.filename == "genes.gtf"
    assert state.timestamp == timestamp
    assert state.timestamp == pytest.approx(time.time(), abs=5)
    assert state.md5 == "d9636a8dca9e5626851471d1c0ea92b1"


def test_update_resource_file_when_state_missing(
        content_fixture: dict[str, Any],
        rw_fsspec_proto: FsspecReadWriteProtocol) -> None:

    # Given
    src_proto = build_inmemory_test_protocol(content_fixture)
    proto = rw_fsspec_proto

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

    assert state is not None
    assert state.filename == "genes.gtf"
    assert state.md5 == "d9636a8dca9e5626851471d1c0ea92b1"
    assert proto.filesystem.modified(fileurl) == timestamp


def test_update_resource_file_when_changed(
        content_fixture: dict[str, Any],
        rw_fsspec_proto: FsspecReadWriteProtocol) -> None:

    # Given
    src_proto = build_inmemory_test_protocol(content_fixture)
    proto = rw_fsspec_proto

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

    assert state is not None
    assert state.filename == "genes.gtf"
    assert state.timestamp == timestamp
    assert state.timestamp == pytest.approx(time.time(), abs=5)

    assert state.md5 == "d9636a8dca9e5626851471d1c0ea92b1"


def test_do_not_update_resource_file_when_state_changed_but_file_not(
        content_fixture: dict[str, Any],
        rw_fsspec_proto: FsspecReadWriteProtocol) -> None:

    # Given
    src_proto = build_inmemory_test_protocol(content_fixture)
    proto = rw_fsspec_proto

    src_res = src_proto.get_resource("sub/two")
    dst_res = proto.get_resource("sub/two")

    state = proto.load_resource_file_state(dst_res, "genes.gtf")
    assert state is not None
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
