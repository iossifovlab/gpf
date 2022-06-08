"""Provides tools usefult for testing."""
from __future__ import annotations

import logging

from typing import Any, cast

from dae.genomic_resources.repository import \
    GenomicResource, \
    GenomicResourceRepo, \
    ReadWriteRepositoryProtocol, \
    parse_gr_id_version_token, \
    is_gr_id_token, \
    GR_CONF_FILE_NAME
from dae.genomic_resources.fsspec_protocol import \
    FsspecReadWriteProtocol, \
    build_fsspec_protocol

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
            if isinstance(content, (str, bytes)):
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


def build_testing_protocol(
        content: dict[str, Any],
        scheme: str = "memory",
        proto_id: str = "testing",
        root_path: str = "/testing",
        **kwargs) -> ReadWriteRepositoryProtocol:
    """Create an embedded or dir GRR protocol using passed content."""
    if not root_path.startswith("/"):
        root_path = f"/{root_path}"

    if scheme == "memory":
        proto = build_fsspec_protocol(
            proto_id, f"memory://{root_path}", **kwargs)
    elif scheme == "file":
        proto = build_fsspec_protocol(
            proto_id, f"file://{root_path}", **kwargs)
    else:
        raise ValueError(f"unsupported testing protocol: {scheme}")

    proto = cast(FsspecReadWriteProtocol, proto)

    for rid, rver, rcontent in _scan_for_resources(content, []):
        resource = GenomicResource(rid, rver, proto)
        for fname, fcontent in _scan_for_resource_files(rcontent, []):
            mode = "wt"
            if isinstance(fcontent, bytes):
                mode = "wb"
            with proto.open_raw_file(resource, fname, mode) as outfile:
                outfile.write(fcontent)
            proto.save_resource_file_state(
                resource, proto.build_resource_file_state(resource, fname))

        proto.save_manifest(resource, proto.build_manifest(resource))

    return proto


def build_testing_repository(
        content: dict[str, Any],
        scheme: str = "memory",
        repo_id: str = "testing",
        root_path: str = "/testing",
        **kwargs) -> GenomicResourceRepo:
    """Create an embedded or dir GRR repository using passed content."""
    proto = build_testing_protocol(
        content, scheme=scheme, proto_id=repo_id,
        root_path=root_path, **kwargs)

    return GenomicResourceRepo(proto)


def build_test_resource(
        content: dict,
        scheme="memory",
        repo_id="testing",
        root_path="/testing",
        **kwargs) -> GenomicResource:
    """Create a resource based on content passed."""
    repo = build_testing_repository(
        content={
            "t": content
        },
        scheme=scheme,
        repo_id=repo_id,
        root_path=root_path,
        **kwargs)
    return repo.get_resource("t")


def tabix_to_resource(tabix_source, resource, filename):
    """Store a tabix file into a resource."""
    tabix_filename, index_filename = tabix_source
    proto = resource.protocol

    with proto.open_raw_file(resource, filename, "wb") as outfile, \
            open(tabix_filename, "rb") as infile:
        data = infile.read()
        outfile.write(data)

    with proto.open_raw_file(resource, f"{filename}.tbi", "wb") as outfile, \
            open(index_filename, "rb") as infile:
        data = infile.read()
        outfile.write(data)

    proto.save_manifest(resource, proto.build_manifest(resource))
    proto.invalidate()
    proto.build_content_file()
