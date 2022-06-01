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
        print(path, content)
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
        proto_id: str, content: dict[str, Any]) -> FsspecReadWriteProtocol:
    """Creates an embedded GRR protocol based on content dictionary passed."""
    filesystem = MemoryFileSystem(skip_instance_cache=True)

    proto = FsspecReadWriteProtocol(
        proto_id, "memory", "", "/test-repo", filesystem)

    for rid, rver, rcontent in _scan_for_resources(content, []):
        resource = GenomicResource(rid, rver, proto)  # type: ignore
        for fname, fcontent in _scan_for_resource_files(rcontent, []):
            with proto.open_raw_file(resource, fname, "wt") as outfile:
                outfile.write(fcontent)
            proto.save_resource_file_state(
                proto.build_resource_file_state(resource, fname))

        proto.save_manifest(resource, proto.build_manifest(resource))

    return proto


# class EmbeddedProtocol(FsspecReadWriteProtocol):
#     """Defines embedded genomic resources protocol."""

#     def __init__(self, proto_id):
#         super().__init__(proto_id, "memory", proto_id, filesystem)

    # def get_all_resources(self):
    #     for resource_id, version in find_genomic_resources_helper(
    #             self.content):
    #         yield self.build_genomic_resource(resource_id, version)

    # def file_exists(self, resource, filename):
    #     try:
    #         self.get_file_content(resource, filename, uncompress=False)
    #         return True
    #     except IOError:
    #         return False

    # def _scan_leaf_content_and_time(
    #         self, leaf_data: Union[list, str]) -> Tuple[str, str]:
    #     if isinstance(leaf_data, list) and len(leaf_data) == 2:
    #         content = leaf_data[0]
    #         timestamp = leaf_data[1]
    #     else:
    #         content = leaf_data
    #         timestamp = self.stable_timestamp
    #     if isinstance(content, str):
    #         content = bytes(content, GR_ENCODING)
    #     return content, timestamp

    # def _scan_resource_file_content_and_time(
    #         self, resource_id: str,
    #         version: Tuple[int, ...],
    #         filename: str):

    #     resource_version_id = \
    #         f"{resource_id}{version_tuple_to_suffix(version)}"
    #     path_array = resource_version_id.split("/")
    #     path_array.extend(filename.split("/"))

    #     data = self.content
    #     for part in path_array[:-1]:
    #         if part == "":
    #             continue
    #         if part not in data or not isinstance(data[part], dict):
    #             logger.error(
    #                 "file <%s> not found in content data: %s", part, data)
    #             raise FileNotFoundError(f"file name <{part}> not found")
    #         data = data[part]
    #     last_part = path_array[-1]
    #     if last_part not in data or isinstance(data[last_part], dict):
    #         raise FileNotFoundError(f"not a valid file name <{last_part}>")

    #     return self._scan_leaf_content_and_time(data[last_part])

    # def load_manifest(self, resource: GenomicResource) -> Manifest:
    #     path_array = resource.get_genomic_resource_id_version().split("/")

    #     content_dict = self.content
    #     for part in path_array:
    #         if part == "":
    #             continue
    #         content_dict = content_dict[part]

    #     def my_leaf_to_size_and_time(leaf_data):
    #         content, timestamp = self._scan_leaf_content_and_time(leaf_data)
    #         return len(content), timestamp

    #     manifest = Manifest()
    #     for fname, fsize, ftime in find_genomic_resource_files_helper(
    #             content_dict, my_leaf_to_size_and_time):
    #         manifest.add(ManifestEntry(
    #             fname, fsize, ftime, self.compute_md5_sum(resource, fname)))
    #     return manifest

    # def open_raw_file(self, resource: GenomicResource, filename: str,
    #                   mode="rt", **kwargs):

    #     content, _timestamp = self._scan_resource_file_content_and_time(
    #         resource.resource_id,
    #         resource.version,
    #         filename)

    #     if "w" in mode:
    #         raise IOError("Can't handle writable files yet!")
    #     if "b" in mode:
    #         return io.BytesIO(content)

    #     return io.StringIO(content.decode(GR_ENCODING))

    # def open_tabix_file(self, resource, filename,
    #                     index_filename=None):
    #     raise NotImplementedError()
