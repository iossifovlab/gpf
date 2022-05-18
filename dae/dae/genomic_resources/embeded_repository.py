"""Provides embeded genomic resources repository useful for testing."""

import io
import time
import hashlib
import gzip
import logging

from .repository import GenomicResource, Manifest, ManifestEntry
from .repository import GenomicResourceRealRepo
from .repository import find_genomic_resources_helper
from .repository import find_genomic_resource_files_helper
from .repository import GR_ENCODING


logger = logging.getLogger(__name__)


class GenomicResourceEmbededRepo(GenomicResourceRealRepo):
    """Defines embeded genomic resources repository."""
    def __init__(self, repo_id, content, **_kwargs):
        super().__init__(repo_id)
        self.content = content
        self.stable_timestamp = ManifestEntry.convert_timestamp(time.time())

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

    def get_file_content(self, resource: GenomicResource, filename,
                         uncompress=True, mode="t"):
        content, _ = self._get_file_content_and_time(resource, filename)

        if uncompress and filename.endswith(".gz"):
            content = gzip.decompress(content)
            if "t" in mode:
                content = content.decode("utf-8")
            return content
        if "t" in mode and isinstance(content, bytes):
            content = content.decode("utf-8")
        return content

    def _get_content_and_time(self, leaf_data):
        if isinstance(leaf_data, list) and len(leaf_data) == 2:
            content = leaf_data[0]
            timestamp = leaf_data[1]
        else:
            content = leaf_data
            timestamp = self.stable_timestamp
        if isinstance(content, str):
            content = bytes(content, GR_ENCODING)
        return content, timestamp

    def _get_file_content_and_time(
            self, resource: GenomicResource, filename: str):

        path_array = resource.get_genomic_resource_id_version().split("/") + \
            filename.split("/")
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

        return self._get_content_and_time(data[last_part])

    def open_raw_file(self, resource, filename,
                      mode=None, uncompress=False, seekable=False):
        content = self.get_file_content(
            resource, filename, uncompress, mode="b")
        if filename.endswith(".gz") and uncompress:
            raise IOError("Can't handle uncompressing gzip files yet!")
        mode = mode if mode else "r"
        if "w" in mode:
            raise IOError("Can't handle writable files yet!")
        if "b" in mode:
            return io.BytesIO(content)

        return io.StringIO(content.decode(GR_ENCODING))

    def get_files(self, resource):
        path_array = resource.get_genomic_resource_id_version().split("/")

        content_dict = self.content
        for token in path_array:
            if token == "":
                continue
            content_dict = content_dict[token]

        def my_leaf_to_size_and_time(val):
            content, timestamp = self._get_content_and_time(val)
            return len(content), timestamp

        yield from find_genomic_resource_files_helper(
            content_dict, my_leaf_to_size_and_time)

    def compute_md5_sum(self, resource, filename):
        """Computes a md5 hash for a file in the resource"""
        with self.open_raw_file(resource, filename, "rb") as infile:
            md5_hash = hashlib.md5()
            while chunk := infile.read(8192):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()

    def get_manifest(self, resource):
        """Builds full manifest for the resource"""

        return Manifest.from_manifest_entries(
            [
                {
                    "name": fn,
                    "size": fs,
                    "time": ft,
                    "md5": self.compute_md5_sum(resource, fn)
                }
                for fn, fs, ft in sorted(self.get_files(resource))])

    def open_tabix_file(self, resource,  filename,
                        index_filename=None):
        raise ValueError(
            "Tabix files are not supported by GenomicResourceEmbededRepo.")
