"""Provides GRR protocols based on fsspec library."""
import os
import pathlib
import hashlib
import logging

from urllib.parse import urlparse
from typing import List, Generator, cast, Union, Optional
from dataclasses import asdict

import fsspec  # type: ignore
import pysam
import yaml

from dae.genomic_resources.repository import Manifest, \
    ReadWriteRepositoryProtocol, \
    ReadOnlyRepositoryProtocol, \
    Mode, \
    ManifestEntry, \
    ResourceFileState, \
    GenomicResource, \
    find_genomic_resources_helper, \
    find_genomic_resource_files_helper, \
    version_string_to_suffix, \
    GR_CONTENTS_FILE_NAME, \
    GR_MANIFEST_FILE_NAME, \
    isoformatted_from_datetime


logger = logging.getLogger(__name__)


class FsspecReadOnlyProtocol(ReadOnlyRepositoryProtocol):
    """Provides fsspec genomic resources repository protocol."""

    def __init__(
            self, proto_id: str,
            root_url: Union[str, pathlib.Path],
            filesystem: fsspec.AbstractFileSystem):

        super().__init__(proto_id)

        if isinstance(root_url, pathlib.Path):
            root_url = str(root_url)

        url = urlparse(root_url)
        self.scheme = url.scheme
        self.location = url.netloc
        self.root_path = os.path.join(self.location, url.path)
        self.state_path = os.path.join(self.root_path, ".grr")

        self.filesystem = filesystem
        self.filesystem.makedirs(self.root_path, exist_ok=True)
        self.filesystem.makedirs(self.state_path, exist_ok=True)
        self.filesystem.touch(
            os.path.join(self.state_path, ".keep"), exist_ok=True)

        self._all_resources: Optional[List[GenomicResource]] = None

    def invalidate(self):
        self._all_resources = None

    def get_all_resources(self):
        """Returns generator for all resources in the repository."""
        if self._all_resources is None:
            self._all_resources = []
            content_filename = os.path.join(
                self.root_path, GR_CONTENTS_FILE_NAME)
            contents = yaml.safe_load(self.filesystem.open(content_filename))

            for entry in contents:
                version = tuple(map(int, entry["version"].split(".")))
                manifest = Manifest.from_manifest_entries(entry["manifest"])
                resource = self.build_genomic_resource(
                    entry["id"], version, config=entry["config"],
                    manifest=manifest)
                logger.debug(
                    "url repo caching resource %s", resource.resource_id)
                self._all_resources.append(resource)

        yield from self._all_resources

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

    def load_manifest(self, resource):
        """Loads resource manifest."""
        content = self.get_file_content(resource, GR_MANIFEST_FILE_NAME)
        return Manifest.from_file_content(content)

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
            compression = "gzip"
        return self.filesystem.open(
            filepath, mode=mode,
            compression=compression)  # pylint: disable=unspecified-encoding

    def open_tabix_file(self, resource, filename,
                        index_filename=None):
        file_path = self.get_resource_file_path(resource, filename)
        index_path = None
        if index_filename:
            index_path = str(self.get_resource_file_path(
                resource, index_filename))
        return pysam.TabixFile(  # pylint: disable=no-member
            file_path, index=index_path)


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

    def _get_filepath_timestamp(self, filepath: str) -> str:
        modification = self.filesystem.modified(filepath)
        return isoformatted_from_datetime(modification)

    def collect_all_resources(self) -> Generator[GenomicResource, None, None]:
        """Returns generator for all resources managed by this protocol."""
        dir_content = self._path_to_dict(self.root_path, self.root_path)
        for res_id, res_ver in find_genomic_resources_helper(dir_content):
            yield self.build_genomic_resource(res_id, res_ver)

    def collect_resource_entries(self, resource) -> List[ManifestEntry]:
        """Scans the resource and resturn list of manifest entries."""
        resource_path = self.get_resource_path(resource)
        content_dict = self._path_to_dict(resource_path)

        def my_leaf_to_size_and_time(filename):
            filepath = self.get_resource_file_path(resource, filename)
            fileinfo = self.filesystem.info(filepath)
            filetime = self._get_filepath_timestamp(filepath)

            return fileinfo["size"], filetime

        result = []
        for fname, fsize, ftime in find_genomic_resource_files_helper(
                content_dict, my_leaf_to_size_and_time):
            result.append(ManifestEntry(fname, fsize, ftime, None))
        return sorted(result)

    def _get_resource_file_state_path(
            self, resource: GenomicResource, filename: str) -> str:
        """Returns filename of the rersource file state path."""
        return os.path.join(
            self.state_path,
            resource.get_genomic_resource_id_version(),
            filename)

    def get_resource_file_timestamp(
            self, resource: GenomicResource, filename: str) -> str:
        path = self.get_resource_file_path(resource, filename)
        return self._get_filepath_timestamp(path)

    def get_resource_file_size(
            self, resource: GenomicResource, filename: str) -> int:
        path = self.get_resource_file_path(resource, filename)
        fileinfo = self.filesystem.info(path)
        return int(fileinfo["size"])

    def save_resource_file_state(
            self, state: ResourceFileState) -> None:
        """Saves resource file state into internal GRR state."""
        path = os.path.join(
            self.state_path,
            f"{state.resource_id}{version_string_to_suffix(state.version)}",
            state.filename)
        if not self.filesystem.exists(os.path.dirname(path)):
            self.filesystem.makedirs(
                os.path.dirname(path), exist_ok=True)

        content = asdict(state)
        with self.filesystem.open(path, "wt", encoding="utf8") as outfile:
            outfile.write(yaml.safe_dump(content))

    def load_resource_file_state(
            self, resource: GenomicResource,
            filename: str) -> Optional[ResourceFileState]:
        """Loads resource file state from internal GRR state.

        If the specified resource file has no internal state returns None."""
        path = self._get_resource_file_state_path(resource, filename)
        if not self.filesystem.exists(path):
            return None
        with self.filesystem.open(path, "rt", encodings="utf8") as infile:
            content = yaml.safe_load(infile.read())
            return ResourceFileState(
                content["resource_id"],
                content["version"],
                content["filename"],
                content["size"],
                content["timestamp"],
                content["md5"]
            )

    def delete_resource_file(
            self, resource: GenomicResource, filename: str):
        """Deletes a resource file and it's internal state."""
        filepath = self.get_resource_file_path(resource, filename)
        if self.filesystem.exists(filepath):
            self.filesystem.delete(filepath)

        statepath = self._get_resource_file_state_path(resource, filename)
        if self.filesystem.exists(statepath):
            self.filesystem.delete(statepath)

    def copy_resource_file(
            self,
            remote_resource: GenomicResource,
            dest_resource: GenomicResource,
            filename: str):
        """Copies a remote resource file into local repository."""
        assert dest_resource.resource_id == remote_resource.resource_id
        assert dest_resource.repo == self

        dest_filepath = self.get_resource_file_path(dest_resource, filename)
        dest_parent = os.path.dirname(dest_filepath)
        if not self.filesystem.exists(dest_parent):
            self.filesystem.mkdir(
                dest_parent, create_parents=True, exist_ok=True)

        logger.debug(
            "copying resource (%s) file: %s",
            remote_resource.resource_id, filename)
        with remote_resource.open_raw_file(
                filename, "rb",
                uncompress=False) as infile, \
                self.open_raw_file(
                    dest_resource,
                    filename, "wb",
                    uncompress=False) as outfile:

            md5_hash = hashlib.md5()
            while chunk := infile.read(32768):
                outfile.write(chunk)
                md5_hash.update(chunk)

        md5 = md5_hash.hexdigest()

        if not self.filesystem.exists(dest_filepath):
            raise IOError(f"destination file not created {dest_filepath}")

        state = self.build_resource_file_state(
            dest_resource,
            filename,
            md5sum=md5)

        self.save_resource_file_state(state)
        return state
