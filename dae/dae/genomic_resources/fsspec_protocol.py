import os
import pathlib
import hashlib
import logging

from urllib.parse import urlparse
from typing import List, Generator, cast, Union, Optional

import fsspec  # type: ignore
import pysam
import yaml

from dae.genomic_resources.repository import Manifest, \
    ReadWriteRepositoryProtocol, \
    ReadOnlyRepositoryProtocol, \
    Mode, \
    ManifestEntry, \
    GenomicResource, \
    find_genomic_resources_helper, \
    find_genomic_resource_files_helper, \
    GR_MANIFEST_FILE_NAME


logger = logging.getLogger(__name__)


class FsspecReadOnlyProtocol(ReadOnlyRepositoryProtocol):
    """Provides fsspec genomic resources repository protocol."""

    def __init__(
            self, proto_id: str, 
            root_url: Union[str, pathlib.Path],
            filesystem: fsspec.AbstractFileSystem,
            **kwargs):

        super().__init__(proto_id)

        if isinstance(root_url, pathlib.Path):
            root_url = str(root_url)

        url = urlparse(root_url)
        self.scheme = url.scheme
        self.location = url.netloc
        self.root_path = os.path.join(self.location, url.path)

        self.filesystem = filesystem
        self.filesystem.makedirs(self.root_path, exist_ok=True)

    def get_resource_path(self, resource) -> str:
        """Returns directory pathlib.Path for specified resources."""
        return os.path.join(
            self.root_path,
            resource.get_genomic_resource_id_version())

    def get_resource_file_path(self, resource, filename: str) -> str:
        """Returns pathlib.Path for a file in a resource."""
        return os.path.join(
            self.get_resource_path(resource), filename)

    def file_exists(self, resource, filename) -> bool:
        filepath = self.get_resource_file_path(resource, filename)
        return cast(bool, self.filesystem.exists(filepath))

    def compute_md5_sum(self, resource, filename):
        """Computes a md5 hash for a file in the resource"""
        logger.debug(
            "compute md5sum for %s in %s", filename, resource.resource_id)
        filepath = self.get_resource_file_path(resource, filename)

        with self.filesystem.open(filepath, "rb") as infile:
            md5_hash = hashlib.md5()
            while chunk := infile.read(8192):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()

    def open_raw_file(self, resource: GenomicResource, filename: str,
                      mode="rt", **kwargs):

        filepath = self.get_resource_file_path(resource, filename)
        if "w" in mode:
            if self.mode() == Mode.READONLY:
                raise IOError(
                    f"Read-Only protocol {self.get_id()} trying to open "
                    f"{filepath} for writing")

            # Create the containing directory if it doesn't exists.
            parent = os.path.dirname(filepath)
            if not self.filesystem.exists(parent):
                self.filesystem.mkdir(
                    parent, create_parents=True, exist_ok=True)

        compression = None
        if kwargs.get("compression"):
            compression="gzip"
        return self.filesystem.open(
            filepath, mode=mode, compression=compression)  # pylint: disable=unspecified-encoding

    def open_tabix_file(self, resource,  filename,
                        index_filename=None):
        file_path = self.get_resource_file_path(resource, filename)
        index_path = None
        if index_filename:
            index_path = str(self.get_resource_file_path(
                resource, index_filename))
        return pysam.TabixFile(file_path, index=index_path)  # pylint: disable=no-member

    def load_manifest(self, resource) -> Manifest:
        """Loads resource manifest"""
        filename = self.get_resource_file_path(resource, GR_MANIFEST_FILE_NAME)
        with self.filesystem.open(filename, "rt", encoding="utf8") as infile:
            content = infile.read()
            return Manifest.from_file_content(content)

    def get_manifest(self, resource):
        """Loads and returnst a resource manifest."""
        manifest = self.load_manifest(resource)
        return manifest


class FsspecReadWriteProtocol(
        FsspecReadOnlyProtocol, ReadWriteRepositoryProtocol):
    """Provides fsspec genomic resources repository protocol."""

    def _path_to_dict(self, parent: str, relative: Optional[str] = None):
        if relative is None:
            relative = parent

        if not self.filesystem.exists(parent):
            return {}
        elif self.filesystem.isdir(parent):
            result = {}
            for entry in self.filesystem.ls(parent, detail=True):
                path = entry["name"]
                if path.startswith(parent):
                    path = os.path.relpath(path, parent)

                if path in {".", ".."}:
                    continue
                if path.startswith("."):
                    continue
                result[path] = self._path_to_dict(entry["name"], parent)
            return result

        return os.path.relpath(parent, relative)

    def collect_all_resources(self) -> Generator[GenomicResource, None, None]:
        """Returns generator for all resources managed by this protocol."""

        dir_content = self._path_to_dict(self.root_path, self.root_path)
        for res_id, res_ver in find_genomic_resources_helper(dir_content):
            yield self.build_genomic_resource(res_id, res_ver)

    def collect_resource_entries(self, resource) -> List[ManifestEntry]:
        """Returns a list of tuples for all files in a resources."""
        resource_path = self.get_resource_path(resource)
        content_dict = self._path_to_dict(resource_path)

        def my_leaf_to_size_and_time(filepath):
            fileinfo = self.filesystem.info(
                os.path.join(resource_path, filepath))
            if self.scheme == "s3":
                timestamp = fileinfo["LastModified"].timestamp()
                filetime = ManifestEntry.convert_timestamp(timestamp)
            elif self.scheme == "":
                # local filesystem
                filetime = ManifestEntry.convert_timestamp(fileinfo["mtime"])
            else:
                filetime = ManifestEntry.convert_timestamp(fileinfo["mtime"])
            return fileinfo["size"], filetime

        result = []
        for fname, fsize, ftime in find_genomic_resource_files_helper(
                content_dict, my_leaf_to_size_and_time):
            result.append(ManifestEntry(fname, fsize, ftime, None))
        return sorted(result)

    def build_manifest(self, resource):
        """Builds full manifest for the resource"""

        manifest = Manifest()
        for entry in self.collect_resource_entries(resource):
            entry.md5 = self.compute_md5_sum(resource, entry.name)
            manifest.add(entry)
        return manifest

    def save_manifest(self, resource, manifest: Manifest):
        """Saves manifest into genomic resources directory."""
        filename = self.get_resource_file_path(resource, GR_MANIFEST_FILE_NAME)
        with self.filesystem.open(filename, "wt", encoding="utf8") as outfile:
            yaml.dump(manifest.to_manifest_entries(), outfile)
        resource.refresh()

    def get_manifest(self, resource):
        """Loads or builds a resource manifest."""
        try:
            manifest = self.load_manifest(resource)
            return manifest
        except FileNotFoundError:
            manifest = self.build_manifest(resource)
            self.save_manifest(resource, manifest)
            return manifest
