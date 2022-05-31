"""Provides embedded genomic resources protocol useful for testing."""

import time
import logging
import io

from typing import Union, Tuple

from dae.genomic_resources.repository import \
    Manifest, \
    ManifestEntry, \
    ReadOnlyRepositoryProtocol, \
    GenomicResource, \
    isoformatted_from_timestamp, \
    find_genomic_resources_helper, \
    find_genomic_resource_files_helper, \
    GR_ENCODING, \
    version_tuple_to_suffix


logger = logging.getLogger(__name__)


class EmbeddedProtocol(ReadOnlyRepositoryProtocol):
    """Defines embedded genomic resources protocol."""

    def __init__(self, repo_id, content, **_kwargs):
        super().__init__(repo_id)
        self.content = content
        self.stable_timestamp = isoformatted_from_timestamp(time.time())

    def get_all_resources(self):
        for resource_id, version in find_genomic_resources_helper(
                self.content):
            yield self.build_genomic_resource(resource_id, version)

    def file_exists(self, resource, filename):
        try:
            self.get_file_content(resource, filename, uncompress=False)
            return True
        except IOError:
            return False

    def _scan_leaf_content_and_time(
            self, leaf_data: Union[list, str]) -> Tuple[str, str]:
        if isinstance(leaf_data, list) and len(leaf_data) == 2:
            content = leaf_data[0]
            timestamp = leaf_data[1]
        else:
            content = leaf_data
            timestamp = self.stable_timestamp
        if isinstance(content, str):
            content = bytes(content, GR_ENCODING)
        return content, timestamp

    def _scan_resource_file_content_and_time(
            self, resource_id: str,
            version: Tuple[int, ...],
            filename: str):

        resource_version_id = \
            f"{resource_id}{version_tuple_to_suffix(version)}"
        path_array = resource_version_id.split("/")
        path_array.extend(filename.split("/"))

        data = self.content
        for part in path_array[:-1]:
            if part == "":
                continue
            if part not in data or not isinstance(data[part], dict):
                logger.error(
                    "file <%s> not found in content data: %s", part, data)
                raise FileNotFoundError(f"file name <{part}> not found")
            data = data[part]
        last_part = path_array[-1]
        if last_part not in data or isinstance(data[last_part], dict):
            raise FileNotFoundError(f"not a valid file name <{last_part}>")

        return self._scan_leaf_content_and_time(data[last_part])

    def load_manifest(self, resource: GenomicResource) -> Manifest:
        path_array = resource.get_genomic_resource_id_version().split("/")

        content_dict = self.content
        for part in path_array:
            if part == "":
                continue
            content_dict = content_dict[part]

        def my_leaf_to_size_and_time(leaf_data):
            content, timestamp = self._scan_leaf_content_and_time(leaf_data)
            return len(content), timestamp

        manifest = Manifest()
        for fname, fsize, ftime in find_genomic_resource_files_helper(
                content_dict, my_leaf_to_size_and_time):
            manifest.add(ManifestEntry(
                fname, fsize, ftime, self.compute_md5_sum(resource, fname)))
        return manifest

    def open_raw_file(self, resource: GenomicResource, filename: str,
                      mode="rt", **kwargs):

        content, _timestamp = self._scan_resource_file_content_and_time(
            resource.resource_id,
            resource.version,
            filename)

        if "w" in mode:
            raise IOError("Can't handle writable files yet!")
        if "b" in mode:
            return io.BytesIO(content)

        return io.StringIO(content.decode(GR_ENCODING))

    def open_tabix_file(self, resource, filename,
                        index_filename=None):
        raise NotImplementedError()
