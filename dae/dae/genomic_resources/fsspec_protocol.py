"""Provides GRR protocols based on fsspec library."""
from __future__ import annotations

import os
import re
import hashlib
import logging

from urllib.parse import urlparse
from typing import List, Generator, cast, Union, Optional
from dataclasses import asdict

import fsspec  # type: ignore
from fsspec.implementations.local import LocalFileSystem  # type: ignore
from fsspec.implementations.http import HTTPFileSystem  # type: ignore
from s3fs.core import S3FileSystem  # type: ignore

import pysam
import yaml

from dae.genomic_resources.repository import GR_CONF_FILE_NAME, Manifest, \
    ReadWriteRepositoryProtocol, \
    ReadOnlyRepositoryProtocol, \
    Mode, \
    ManifestEntry, \
    ResourceFileState, \
    GenomicResource, isoformatted_from_datetime, \
    isoformatted_from_timestamp, \
    version_string_to_suffix, \
    GR_CONTENTS_FILE_NAME, \
    GR_MANIFEST_FILE_NAME


logger = logging.getLogger(__name__)


def build_fsspec_protocol(proto_id: str, root_url: str, **kwargs) -> Union[
        FsspecReadOnlyProtocol, FsspecReadWriteProtocol]:
    """Create fsspec GRR protocol based on the root url."""
    url = urlparse(root_url)
    # pylint: disable=import-outside-toplevel

    if url.scheme in {"file", ""}:
        filesystem = LocalFileSystem()
        return FsspecReadWriteProtocol(
            proto_id, root_url, filesystem)

    if url.scheme in {"http": "https"}:
        base_url = kwargs.get("base_url")
        filesystem = HTTPFileSystem(client_kwargs={"base_url": base_url})
        return FsspecReadOnlyProtocol(proto_id, root_url, filesystem)

    if url.scheme in {"s3"}:
        filesystem = kwargs.get("filesystem")
        if filesystem is None:
            endpoint_url = kwargs.get("endpoint_url")
            filesystem = S3FileSystem(
                anon=False, client_kwargs={"endpoint_url": endpoint_url})
        return FsspecReadWriteProtocol(
            proto_id, root_url, filesystem)

    raise NotImplementedError(f"unsupported schema {url.scheme}")


class FsspecReadOnlyProtocol(ReadOnlyRepositoryProtocol):
    """Provides fsspec genomic resources repository protocol."""

    def __init__(
            self, proto_id: str,
            url: str,
            filesystem: fsspec.AbstractFileSystem):

        super().__init__(proto_id)

        parsed = urlparse(url)
        self.scheme = parsed.scheme
        if self.scheme == "":
            self.scheme = "file"
        self.netloc = parsed.netloc
        self.root_path = parsed.path
        if not self.root_path.startswith("/"):
            self.root_path = f"/{self.root_path}"

        self.url = f"{self.scheme}://{self.netloc}{self.root_path}"
        self.filesystem = filesystem

        self._all_resources: Optional[List[GenomicResource]] = None

    def invalidate(self):
        self._all_resources = None

    def get_all_resources(self):
        """Return generator over all resources in the repository."""
        if self._all_resources is None:
            self._all_resources = []
            content_filename = os.path.join(
                self.url, GR_CONTENTS_FILE_NAME)
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

    def get_resource_url(self, resource) -> str:
        """Return url of the specified resources."""
        resource_url = os.path.join(
            self.url,
            resource.get_genomic_resource_id_version())
        return resource_url

    def get_resource_file_url(self, resource, filename: str) -> str:
        """Return url of a file in the resource."""
        url = os.path.join(
            self.get_resource_url(resource), filename)
        return url

    def file_exists(self, resource, filename) -> bool:
        filepath = self.get_resource_file_url(resource, filename)
        return cast(bool, self.filesystem.exists(filepath))

    def load_manifest(self, resource):
        """Load resource manifest."""
        content = self.get_file_content(resource, GR_MANIFEST_FILE_NAME)
        return Manifest.from_file_content(content)

    def open_raw_file(self, resource: GenomicResource, filename: str,
                      mode="rt", **kwargs):

        filepath = self.get_resource_file_url(resource, filename)
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

        if self.scheme not in {"file", "s3", "http", "https"}:
            raise IOError(
                f"tabix files are not supported on schema {self.scheme}")

        def process_tabix_url(url):
            if self.scheme == "file":
                return urlparse(url).path
            if self.scheme == "s3":
                return self.filesystem.sign(url)
            return url

        file_url = process_tabix_url(
            self.get_resource_file_url(resource, filename))

        if index_filename is None:
            index_filename = f"{filename}.tbi"
        index_url = process_tabix_url(
            self.get_resource_file_url(resource, index_filename))

        return pysam.TabixFile(  # pylint: disable=no-member
            file_url, index=index_url)


_RESOURCE_ID_WITH_VERSION_TOKEN_RE = re.compile(
    r"([a-zA-Z0-9/._-]+)(?:\(([1-9]\d*(?:\.\d+)*)\))?")


def parse_resource_id_version(resource_path):
    """Parse genomic resource id and version path into Id, Version tuple.

    An optional version (0,) appened if needed. If present, the version suffix
    has the form "(3.3.2)". The default version is (0,).
    Returns tuple (None, None) if the path does not match the
    resource_id/version requirements. Otherwise returns tuple
    (resource_id, version).
    """
    match = _RESOURCE_ID_WITH_VERSION_TOKEN_RE.fullmatch(resource_path)
    if not match:
        return None, None
    token = match[1]
    version_string = match[2]
    if version_string:
        version = tuple(map(int, version_string.split(".")))
    else:
        version = (0,)
    return token, version


class FsspecReadWriteProtocol(
        FsspecReadOnlyProtocol, ReadWriteRepositoryProtocol):
    """Provides fsspec genomic resources repository protocol."""

    def __init__(
            self, proto_id: str,
            url: str,
            filesystem: fsspec.AbstractFileSystem):

        super().__init__(proto_id, url, filesystem)

        self.filesystem.makedirs(self.url, exist_ok=True)

        self.state_url = os.path.join(self.url, ".grr")
        self.filesystem.makedirs(self.state_url, exist_ok=True)
        self.filesystem.touch(
            os.path.join(self.state_url, ".keep"), exist_ok=True)

    def _scan_path_for_resources(self, path_array):

        url = os.path.join(self.url, *path_array)
        path = os.path.join(self.root_path, *path_array)
        assert isinstance(url, str)

        if not self.filesystem.isdir(url):
            return

        content = []
        for direntry in self.filesystem.ls(url):
            if self.netloc and direntry.startswith(self.netloc):
                direntry = direntry[len(self.netloc):]
            name = os.path.relpath(direntry, path)
            if name.startswith("."):
                continue
            content.append(name)

        if GR_CONF_FILE_NAME in content:
            res_path = "/".join(path_array)
            resource_id, version = parse_resource_id_version(res_path)
            if resource_id is None:
                logger.error("bad resource id/version: %s", res_path)
                return
            yield resource_id, version, res_path
        else:
            for name in content:
                yield from self._scan_path_for_resources([*path_array, name])

    def _scan_resource_for_files(self, resource_path, path_array):

        url = os.path.join(self.url, resource_path, *path_array)
        if not self.filesystem.isdir(url):
            if path_array:
                yield os.path.join(*path_array), url
            return

        path = os.path.join(self.root_path, resource_path, *path_array)
        content = []
        for direntry in self.filesystem.ls(url):
            if self.netloc and direntry.startswith(self.netloc):
                direntry = direntry[len(self.netloc):]

            name = os.path.relpath(direntry, path)
            if name.startswith("."):
                continue
            content.append(name)

        for name in content:
            yield from self._scan_resource_for_files(
                resource_path, [*path_array, name])

    def _get_filepath_timestamp(self, filepath: str) -> str:
        try:
            modification = self.filesystem.modified(filepath)
            return isoformatted_from_datetime(modification)
        except NotImplementedError:
            info = self.filesystem.info(filepath)
            modification = info.get("created")
            return isoformatted_from_timestamp(modification)

    def collect_all_resources(self) -> Generator[GenomicResource, None, None]:
        """Return generator over all resources managed by this protocol."""
        for res_id, res_ver, res_path in self._scan_path_for_resources([]):
            res_fullpath = os.path.join(self.root_path, res_path)
            assert res_fullpath.startswith("/")
            res_fullpath = f"{self.scheme}://{self.netloc}{res_fullpath}"

            with self.filesystem.open(
                    os.path.join(
                        res_fullpath, GR_CONF_FILE_NAME), "rt") as infile:
                config = yaml.safe_load(infile)

            manifest: Optional[Manifest] = None
            manifest_filename = os.path.join(
                res_fullpath, GR_MANIFEST_FILE_NAME)
            if self.filesystem.exists(manifest_filename):
                with self.filesystem.open(manifest_filename, "rt") as infile:
                    manifest = Manifest.from_file_content(infile.read())
            yield self.build_genomic_resource(
                res_id, res_ver, config, manifest)

    def collect_resource_entries(self, resource) -> Manifest:
        """Scan the resource and resturn a manifest."""
        resource_path = resource.get_genomic_resource_id_version()

        result = Manifest()
        for name, path in self._scan_resource_for_files(resource_path, []):
            timestamp = self._get_filepath_timestamp(path)
            size = self._get_filepath_size(path)
            result.add(ManifestEntry(
                name, size, timestamp, None))
        return result

    def get_all_resources(self) -> Generator[GenomicResource, None, None]:
        """Return generator over all resources in the repository."""
        if self._all_resources is None:
            self._all_resources = list(self.collect_all_resources())
        yield from self._all_resources

    def _get_resource_file_state_path(
            self, resource: GenomicResource, filename: str) -> str:
        """Return filename of the rersource file state path."""
        return os.path.join(
            self.state_url,
            resource.get_genomic_resource_id_version(),
            filename)

    def get_resource_file_timestamp(
            self, resource: GenomicResource, filename: str) -> str:
        url = self.get_resource_file_url(resource, filename)
        return self._get_filepath_timestamp(url)

    def _get_filepath_size(
            self, filepath: str) -> int:
        fileinfo = self.filesystem.info(filepath)
        return int(fileinfo["size"])

    def get_resource_file_size(
            self, resource: GenomicResource, filename: str) -> int:
        path = self.get_resource_file_url(resource, filename)
        return self._get_filepath_size(path)

    def save_resource_file_state(
            self, state: ResourceFileState) -> None:
        """Save resource file state into internal GRR state."""
        path = os.path.join(
            self.state_url,
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
        """Load resource file state from internal GRR state.

        If the specified resource file has no internal state returns None.
        """
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
        """Delete a resource file and it's internal state."""
        filepath = self.get_resource_file_url(resource, filename)
        if self.filesystem.exists(filepath):
            self.filesystem.delete(filepath)

        statepath = self._get_resource_file_state_path(resource, filename)
        if self.filesystem.exists(statepath):
            self.filesystem.delete(statepath)

    def copy_resource_file(
            self,
            remote_resource: GenomicResource,
            dest_resource: GenomicResource,
            filename: str) -> ResourceFileState:
        """Copy a resource file into repository."""
        assert dest_resource.resource_id == remote_resource.resource_id
        assert dest_resource.repo == self
        remote_manifest = remote_resource.get_manifest()
        if filename not in remote_manifest:
            raise FileNotFoundError(
                f"{filename} not found in remote resource "
                f"{remote_resource.resource_id}")
        manifest_entry = remote_manifest[filename]

        dest_filepath = self.get_resource_file_url(dest_resource, filename)
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

        if md5 != manifest_entry.md5:
            raise IOError(
                f"file copy is broken; md5sum are different: "
                f"{md5}!={manifest_entry.md5}")

        state = self.build_resource_file_state(
            dest_resource,
            filename,
            md5sum=md5)

        self.save_resource_file_state(state)
        return state

    def update_resource_file(
            self, remote_resource: GenomicResource,
            dest_resource: GenomicResource,
            filename: str) -> ResourceFileState:
        """Update a resource file into repository if needed."""
        assert dest_resource.resource_id == remote_resource.resource_id
        assert dest_resource.repo == self

        local_state = self.load_resource_file_state(dest_resource, filename)
        if local_state is None:
            return self.copy_resource_file(
                remote_resource, dest_resource, filename)

        timestamp = self.get_resource_file_timestamp(dest_resource, filename)
        size = self.get_resource_file_size(dest_resource, filename)
        if timestamp != local_state.timestamp or \
                size != local_state.size:
            return self.copy_resource_file(
                remote_resource, dest_resource, filename)

        remote_manifest = remote_resource.get_manifest()
        if filename not in remote_manifest:
            raise FileNotFoundError(
                f"{filename} not found in remote resource "
                f"{remote_resource.resource_id}")
        manifest_entry = remote_manifest[filename]
        if local_state.md5 != manifest_entry.md5:
            return self.copy_resource_file(
                remote_resource, dest_resource, filename)

        return local_state

    def build_content_file(self):
        """Build the content of the repository - .CONTENTS file."""

        content = [
            {
                "id": gr.resource_id,
                "version": gr.get_version_str(),
                "config": gr.get_config(),
                "manifest": gr.get_manifest().to_manifest_entries()
            }
            for gr in self.get_all_resources()]
        content = sorted(content, key=lambda x: x["id"])

        content_filepath = os.path.join(
            self.url, GR_CONTENTS_FILE_NAME)
        with self.filesystem.open(
                content_filepath, "wt", encoding="utf8") as outfile:
            yaml.dump(content, outfile)

        return content
