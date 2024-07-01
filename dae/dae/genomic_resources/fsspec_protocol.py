"""Provides GRR protocols based on fsspec library."""
from __future__ import annotations

import datetime
import fcntl
import hashlib
import logging
import operator
import os
from collections.abc import Generator
from contextlib import AbstractContextManager
from dataclasses import asdict
from types import TracebackType
from typing import (
    IO,
    Any,
    Optional,
    Union,
    cast,
)
from urllib.parse import urlparse

import fsspec
import jinja2
import pyBigWig  # type: ignore
import pysam
import yaml

from dae.genomic_resources.repository import (
    GR_CONF_FILE_NAME,
    GR_CONTENTS_FILE_NAME,
    GR_INDEX_FILE_NAME,
    GR_MANIFEST_FILE_NAME,
    GenomicResource,
    Manifest,
    ManifestEntry,
    Mode,
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
    ResourceFileState,
    is_gr_id_token,
    parse_gr_id_version_token,
    parse_resource_id_version,
)
from dae.utils.helpers import convert_size

logger = logging.getLogger(__name__)


def _scan_for_resources(
    content_dict: dict, parent_id: list[str],
) -> Generator[tuple[str, tuple[int, ...], dict], None, None]:
    name = "/".join(parent_id)
    id_ver = parse_gr_id_version_token(name)
    if isinstance(content_dict, dict) and id_ver and \
            GR_CONF_FILE_NAME in content_dict and \
            not isinstance(content_dict[GR_CONF_FILE_NAME], dict):
        # resource found
        resource_id, version = id_ver
        yield "/".join([*parent_id, resource_id]), version, content_dict
        return

    for name, content in content_dict.items():
        id_ver = parse_gr_id_version_token(name)
        if isinstance(content, dict) and id_ver and \
                GR_CONF_FILE_NAME in content and \
                not isinstance(content[GR_CONF_FILE_NAME], dict):
            # resource found
            resource_id, version = id_ver
            yield "/".join([*parent_id, resource_id]), version, content
        else:
            curr_id = [*parent_id, name]
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
            yield from _scan_for_resources(content, curr_id)


def _scan_for_resource_files(
    content_dict: dict[str, Any], parent_dirs: list[str],
) -> Generator[tuple[str, Union[str, bytes]], None, None]:

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
                raise TypeError(f"unexpected content at {fname}: {content}")


def build_inmemory_protocol(
        proto_id: str,
        root_path: str,
        content: dict[str, Any]) -> FsspecReadWriteProtocol:
    """Build and return an embedded fsspec protocol for testing."""
    if not os.path.isabs(root_path):
        logger.error(
            "for embedded resources repository we expects an "
            "absolute path: %s", root_path)
        raise ValueError(f"not an absolute root path: {root_path}")

    proto = cast(
        FsspecReadWriteProtocol,
        build_fsspec_protocol(proto_id, f"memory://{root_path}"))
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


class FsspecReadOnlyProtocol(ReadOnlyRepositoryProtocol):
    """Provides fsspec genomic resources repository protocol."""

    def __init__(
            self, proto_id: str,
            url: str,
            filesystem: fsspec.AbstractFileSystem):

        super().__init__(proto_id, url)

        parsed = urlparse(url)
        self.scheme = parsed.scheme
        if self.scheme == "":
            self.scheme = "file"
        self.netloc = parsed.netloc
        self.root_path = parsed.path

        self.url = f"{self.scheme}://{self.netloc}{self.root_path}"
        self.filesystem = filesystem

        self._all_resources: Optional[list[GenomicResource]] = None

    def get_url(self) -> str:
        return self.url

    def invalidate(self) -> None:
        self._all_resources = None

    def get_all_resources(self) -> Generator[GenomicResource, None, None]:
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
            self._all_resources = sorted(
                self._all_resources,
                key=lambda r: r.get_genomic_resource_id_version())

        yield from self._all_resources

    def file_exists(
            self, resource: GenomicResource, filename: str) -> bool:
        filepath = self.get_resource_file_url(resource, filename)
        return cast(bool, self.filesystem.exists(filepath))

    def load_manifest(self, resource: GenomicResource) -> Manifest:
        """Load resource manifest."""
        content = self.get_file_content(resource, GR_MANIFEST_FILE_NAME)
        return Manifest.from_file_content(content)

    def open_raw_file(
            self, resource: GenomicResource, filename: str,
            mode: str = "rt", **kwargs: Union[str, bool, None]) -> IO:

        filepath = self.get_resource_file_url(resource, filename)
        if "w" in mode:
            if self.mode() == Mode.READONLY:
                raise OSError(
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

        return cast(
            IO,
            self.filesystem.open(
                filepath, mode=mode,
                compression=compression))

    def _get_file_url(self, resource: GenomicResource, filename: str) -> str:
        def process_file_url(url: str) -> str:
            if self.scheme == "file":
                return urlparse(url).path
            if self.scheme == "s3":
                return cast(str, self.filesystem.sign(url))
            return url

        return process_file_url(self.get_resource_file_url(resource, filename))

    def open_tabix_file(
            self, resource: GenomicResource,
            filename: str,
            index_filename: Optional[str] = None) -> pysam.TabixFile:

        if self.scheme not in {"file", "s3", "http", "https"}:
            raise OSError(
                f"tabix files are not supported on schema {self.scheme}")

        file_url = self._get_file_url(resource, filename)

        if index_filename is None:
            index_filename = f"{filename}.tbi"
        index_url = self._get_file_url(resource, index_filename)

        return pysam.TabixFile(  # pylint: disable=no-member
            file_url, index=index_url, encoding="utf-8",
            parser=pysam.asTuple())

    def open_vcf_file(
            self, resource: GenomicResource,
            filename: str,
            index_filename: Optional[str] = None) -> pysam.VariantFile:

        if self.scheme not in {"file", "s3", "http", "https"}:
            raise OSError(
                f"vcf files are not supported on schema {self.scheme}")

        file_url = self._get_file_url(resource, filename)

        if index_filename is None:
            index_filename = f"{filename}.tbi"
        index_url = self._get_file_url(resource, index_filename)

        return pysam.VariantFile(  # pylint: disable=no-member
            file_url, index_filename=index_url)

    def open_bigwig_file(
        self, resource: GenomicResource, filename: str) -> Any:
        if self.scheme not in {"file", "s3", "http", "https"}:
            raise OSError(
                f"bigwig files are not supported on schema {self.scheme}")
        file_url = self._get_file_url(resource, filename)
        return pyBigWig.open(file_url)  # pylint: disable=I1101


class FsspecReadWriteProtocol(
        FsspecReadOnlyProtocol, ReadWriteRepositoryProtocol):
    """Provides fsspec genomic resources repository protocol."""

    def __init__(
            self, proto_id: str,
            url: str,
            filesystem: fsspec.AbstractFileSystem):

        super().__init__(proto_id, url, filesystem)

        self.filesystem.makedirs(self.url, exist_ok=True)

    def _get_resource_file_lockfile_path(
        self, resource: GenomicResource, filename: str,
    ) -> str:
        """Return path of the resource file's lockfile."""
        if self.scheme != "file":
            raise NotImplementedError
        resource_url = self.get_resource_url(resource)
        path = os.path.join(resource_url, ".grr", f"{filename}.lockfile")
        return path.removeprefix(f"{self.scheme}://")

    def obtain_resource_file_lock(
        self, resource: GenomicResource, filename: str,
    ) -> AbstractContextManager:
        """Lock a resource's file."""

        class Lock:
            """Lock representation."""

            def __enter__(self) -> None:
                pass

            def __exit__(
                    self,
                    exc_type: type[BaseException] | None,
                    exc_value: Optional[BaseException],
                    exc_tb: TracebackType | None) -> None:
                pass

        lock = Lock()

        if self.scheme == "file":
            path = self._get_resource_file_lockfile_path(resource, filename)
            if not self.filesystem.exists(os.path.dirname(path)):
                self.filesystem.makedirs(
                    os.path.dirname(path), exist_ok=True)
            # pylint: disable=consider-using-with
            lockfile = open(path, "wt", encoding="utf8")  # noqa
            lockfile.write(str(datetime.datetime.now()) + "\n")
            fcntl.flock(lockfile, fcntl.LOCK_EX)
            lock.__enter__ = lockfile.__enter__  # type: ignore
            lock.__exit__ = lockfile.__exit__  # type: ignore

        return lock

    def _scan_path_for_resources(
        self, path_array: list[str],
    ) -> Generator[Any, None, None]:

        url = os.path.join(self.url, *path_array)
        path = os.path.join(self.root_path, *path_array)
        assert isinstance(url, str)

        if not self.filesystem.isdir(url):
            return

        content = []
        for direntry in self.filesystem.ls(url, detail=False):
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

    def _scan_resource_for_files(
        self, resource_path: str, path_array: list[str],
    ) -> Generator[Any, None, None]:

        url = os.path.join(self.url, resource_path, *path_array)
        if not self.filesystem.isdir(url):
            if path_array:
                yield os.path.join(*path_array), url
            return

        path = os.path.join(self.root_path, resource_path, *path_array)
        content = []
        for direntry in self.filesystem.ls(url, detail=False):
            if self.netloc and direntry.startswith(self.netloc):
                direntry = direntry[len(self.netloc):]

            name = os.path.relpath(direntry, path)
            if name.startswith("."):
                continue
            content.append(name)

        for name in content:
            yield from self._scan_resource_for_files(
                resource_path, [*path_array, name])

    def _get_filepath_timestamp(self, filepath: str) -> float:
        try:
            modification = self.filesystem.modified(filepath)
            modification = modification.replace(tzinfo=datetime.timezone.utc)
            return cast(float, round(modification.timestamp(), 2))
        except NotImplementedError:
            info = self.filesystem.info(filepath)
            modification = info.get("created")
            return cast(float, round(modification, 2))

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

    def collect_resource_entries(self, resource: GenomicResource) -> Manifest:
        """Scan the resource and resturn a manifest."""
        resource_path = resource.get_genomic_resource_id_version()

        result = Manifest()
        for name, path in self._scan_resource_for_files(resource_path, []):
            size = self._get_filepath_size(path)
            result.add(ManifestEntry(name, size, None))
        return result

    def get_all_resources(self) -> Generator[GenomicResource, None, None]:
        """Return generator over all resources in the repository."""
        if self._all_resources is None:
            self._all_resources = sorted(
                self.collect_all_resources(),
                key=lambda r: r.get_genomic_resource_id_version())

        yield from self._all_resources

    def _get_resource_file_state_path(
            self, resource: GenomicResource, filename: str) -> str:
        """Return filename of the resource file state path."""
        resource_url = self.get_resource_url(resource)
        return os.path.join(resource_url, ".grr", f"{filename}.state")

    def get_resource_file_timestamp(
            self, resource: GenomicResource, filename: str) -> float:
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
            self, resource: GenomicResource, state: ResourceFileState) -> None:
        """Save resource file state into internal GRR state."""
        path = self._get_resource_file_state_path(resource, state.filename)
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
                content["filename"],
                content["size"],
                content["timestamp"],
                content["md5"],
            )

    def delete_resource_file(
            self, resource: GenomicResource, filename: str) -> None:
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
            filename: str) -> Optional[ResourceFileState]:
        """Copy a resource file into repository."""
        assert dest_resource.resource_id == remote_resource.resource_id
        logger.debug(
            "copying resource file (%s: %s) from %s",
            remote_resource.resource_id, filename,
            remote_resource.proto.proto_id)
        remote_manifest = remote_resource.get_manifest()
        if filename not in remote_manifest:
            self.delete_resource_file(dest_resource, filename)
            return None

        manifest_entry = remote_manifest[filename]

        dest_filepath = self.get_resource_file_url(dest_resource, filename)
        dest_parent = os.path.dirname(dest_filepath)
        if not self.filesystem.exists(dest_parent):
            self.filesystem.mkdir(
                dest_parent, create_parents=True, exist_ok=True)

        with remote_resource.open_raw_file(
                filename, "rb",
                uncompress=False) as infile, \
                self.open_raw_file(
                    dest_resource,
                    filename, "wb",
                    uncompress=False) as outfile:

            md5_hash = hashlib.md5()  # noqa
            while chunk := infile.read(self.CHUNK_SIZE):
                outfile.write(chunk)
                md5_hash.update(chunk)

        md5 = md5_hash.hexdigest()

        if not self.filesystem.exists(dest_filepath):
            raise OSError(f"destination file not created {dest_filepath}")

        if md5 != manifest_entry.md5:
            raise OSError(
                f"file copy is broken "
                f"{dest_resource.resource_id} ({filename}); "
                f"md5sum are different: "
                f"{md5}!={manifest_entry.md5}")

        state = self.build_resource_file_state(
            dest_resource,
            filename,
            md5sum=md5)

        self.save_resource_file_state(dest_resource, state)

        return state

    def update_resource_file(
            self, remote_resource: GenomicResource,
            dest_resource: GenomicResource,
            filename: str) -> Optional[ResourceFileState]:
        """Update a resource file into repository if needed."""
        assert dest_resource.resource_id == remote_resource.resource_id

        if not self.file_exists(dest_resource, filename):
            return self.copy_resource_file(
                remote_resource, dest_resource, filename)

        local_state = self.load_resource_file_state(dest_resource, filename)
        if local_state is None:
            local_state = self.build_resource_file_state(
                dest_resource, filename)
            self.save_resource_file_state(dest_resource, local_state)
        else:
            timestamp = self.get_resource_file_timestamp(
                dest_resource, filename)
            size = self.get_resource_file_size(dest_resource, filename)
            if timestamp != local_state.timestamp or \
                    size != local_state.size:
                local_state = self.build_resource_file_state(
                    dest_resource, filename)
                self.save_resource_file_state(dest_resource, local_state)

        remote_manifest = remote_resource.get_manifest()
        if filename not in remote_manifest:
            self.delete_resource_file(dest_resource, filename)
            return None
        manifest_entry = remote_manifest[filename]
        if local_state.md5 != manifest_entry.md5:
            return self.copy_resource_file(
                remote_resource, dest_resource, filename)

        return local_state

    def build_content_file(self) -> list[dict[str, Any]]:
        """Build the content of the repository (i.e '.CONTENTS' file)."""
        content = [
            {
                "id": res.resource_id,
                "version": res.get_version_str(),
                "config": res.get_config(),
                "manifest": res.get_manifest().to_manifest_entries(),
            }
            for res in self.get_all_resources()]
        content = sorted(content, key=operator.itemgetter("id"))  # type: ignore

        content_filepath = os.path.join(
            self.url, GR_CONTENTS_FILE_NAME)
        with self.filesystem.open(
                content_filepath, "wt", encoding="utf8") as outfile:
            yaml.dump(content, outfile)

        return content

    def build_index_info(self, repository_template: jinja2.Template) -> dict:
        """Build info dict for the repository."""
        result = {}
        for res in self.get_all_resources():
            res_size = convert_size(
                sum(f for _, f in res.get_manifest().get_files()),
            )
            assert res.config is not None
            result[res.get_full_id()] = {
                **res.config,
                "res_version": res.get_version_str(),
                "res_files": len(list(res.get_manifest().get_files())),
                "res_size": res_size,
                "res_summary": res.get_summary(),
            }

        content_filepath = os.path.join(self.url, GR_INDEX_FILE_NAME)
        with self.filesystem.open(
                content_filepath, "wt", encoding="utf8") as outfile:
            outfile.write(repository_template.render(data=result))

        return result


def build_local_resource(
        dirname: str, config: dict[str, Any]) -> GenomicResource:
    """Build a resource from a local filesystem directory."""
    proto = build_fsspec_protocol("d", dirname)
    return GenomicResource(".", (0, ), proto, config)


FsspecRepositoryProtocol = Union[
    FsspecReadOnlyProtocol, FsspecReadWriteProtocol]


def build_fsspec_protocol(
    proto_id: str, root_url: str, **kwargs: Union[str, None],
) -> FsspecRepositoryProtocol:
    """Create fsspec GRR protocol based on the root url."""
    url = urlparse(root_url)
    # pylint: disable=import-outside-toplevel

    if url.scheme in {"file", ""}:
        from fsspec.implementations.local import LocalFileSystem
        filesystem = LocalFileSystem()
        return FsspecReadWriteProtocol(
            proto_id, root_url, filesystem)
    if url.scheme in {"http", "https"}:
        from fsspec.implementations.http import HTTPFileSystem
        base_url = kwargs.get("base_url")
        filesystem = HTTPFileSystem(client_kwargs={"base_url": base_url})
        return FsspecReadOnlyProtocol(proto_id, root_url, filesystem)

    if url.scheme == "s3":
        filesystem = kwargs.get("filesystem")
        if filesystem is None:
            from s3fs.core import S3FileSystem

            endpoint_url = kwargs.get("endpoint_url")
            filesystem = S3FileSystem(
                anon=False, client_kwargs={"endpoint_url": endpoint_url})
        return FsspecReadWriteProtocol(
            proto_id, root_url, filesystem)
    if url.scheme == "memory":
        from fsspec.implementations.memory import MemoryFileSystem
        filesystem = MemoryFileSystem()
        return FsspecReadWriteProtocol(proto_id, root_url, filesystem)

    raise NotImplementedError(f"unsupported schema {url.scheme}")
