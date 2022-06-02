"""Provides embedded genomic resources protocol useful for testing."""
from __future__ import annotations

import logging

from typing import Any

from fsspec.implementations.memory import MemoryFileSystem  # type: ignore

from dae.genomic_resources.repository import \
    GenomicResource, \
    parse_gr_id_version_token, \
    is_gr_id_token, \
    GR_CONF_FILE_NAME
from dae.genomic_resources.fsspec_protocol import \
    FsspecReadWriteProtocol


logger = logging.getLogger(__name__)


def _scan_for_resource_files(content_dict: dict[str, Any], parent_dirs):

    for path, content in content_dict.items():
        if isinstance(content, dict):
            # handle subdirectory
            for fname, fcontent in _scan_for_resource_files(
                    content, [*parent_dirs, path]):
                yield fname, fcontent
        else:
            fname = "/".join([*parent_dirs, path])
            if isinstance(content, str):
                # handle file content
                yield fname, content
            else:
                logger.error(
                    "unexpected content at %s: %s", fname, content)
                raise ValueError(f"unexpected content at {fname}: {content}")


def _scan_for_resources(content_dict, parent_id):

    for name, content in content_dict.items():
        id_ver = parse_gr_id_version_token(name)
        if isinstance(content, dict) and id_ver and \
                GR_CONF_FILE_NAME in content and \
                not isinstance(content[GR_CONF_FILE_NAME], dict):
            # resource found
            resource_id, version = id_ver
            yield "/".join([*parent_id, resource_id]), version, content
        else:
            curr_id = parent_id + [name]
            curr_id_path = "/".join(curr_id)
            if not isinstance(content, dict):
                logger.warning("file <%s> is not used.", curr_id_path)
                continue
            if not is_gr_id_token(name):
                logger.warning(
                    "directory <%s> has a name <%s> that is not a "
                    "valid Genomic Resource Id Token.", curr_id_path, name)
                continue

            # scan children
            for rid, rver, rcontent in _scan_for_resources(content, curr_id):
                yield rid, rver, rcontent


def build_embedded_protocol(
        proto_id: str,
        root_path: str,
        content: dict[str, Any]) -> FsspecReadWriteProtocol:
    """Create an embedded GRR protocol based on content dictionary passed."""
    filesystem = MemoryFileSystem(skip_instance_cache=True)

    if not root_path.startswith("/"):
        root_path = f"/{root_path}"

    proto = FsspecReadWriteProtocol(
        proto_id, f"memory://{root_path}", filesystem)

    for rid, rver, rcontent in _scan_for_resources(content, []):
        resource = GenomicResource(rid, rver, proto)  # type: ignore
        for fname, fcontent in _scan_for_resource_files(rcontent, []):
            with proto.open_raw_file(resource, fname, "wt") as outfile:
                outfile.write(fcontent)
            proto.save_resource_file_state(
                proto.build_resource_file_state(resource, fname))

        proto.save_manifest(resource, proto.build_manifest(resource))

    return proto
