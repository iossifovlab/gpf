"""
Provides basic classes for genomic resources and repositories.

       +---------------------+                    +-----------------+
 +-----| GenomicResourceRepo |--------------------| GenomicResource |
 |     +---------------------+                    +-----------------+
 |        ^               ^                                    |
 |        |               |                                    |
 |        |  +-----------------------------+     +----------------------------+
 |        |  | GenomicResourceProtocolRepo | ----| ReadOnlyRepositoryProtocol |
 |        |  +-----------------------------+     +----------------------------+
 |        |                                                    ^
 |        |                                                    |
 |    +--------------------------+            +-----------------------------+
 +----| GenomicResourceGroupRepo |            | ReadWriteRepositoryProtocol |
      +--------------------------+            +-----------------------------+


"""
from __future__ import annotations

import abc
import copy
import enum
import hashlib
import logging
import os
import re
from collections.abc import Generator, Iterator
from dataclasses import asdict, dataclass
from typing import IO, Any, cast

import pysam
import yaml

logger = logging.getLogger(__name__)


GR_CONF_FILE_NAME = "genomic_resource.yaml"
GR_MANIFEST_FILE_NAME = ".MANIFEST"
GR_CONTENTS_FILE_NAME = ".CONTENTS.json"
GR_INDEX_FILE_NAME = "index.html"

GR_ENCODING = "utf-8"

_GR_ID_TOKEN_RE = re.compile(r"[a-zA-Z0-9._-]+")


def is_gr_id_token(token: str) -> bool:
    """Check if token can be used as a genomic resource ID.

    Genomic Resource Id Token is a string with one or more letters,
    numbers, '.', '_', or '-'. The function checks if the parameter
    token is a Genomic REsource Id Token.
    """
    return bool(_GR_ID_TOKEN_RE.fullmatch(token))


_GR_ID_WITH_VERSION_TOKEN_RE = re.compile(
    r"([a-zA-Z0-9._-]+)(?:\(([1-9]\d*(?:\.\d+)*)\))?")


def parse_gr_id_version_token(token: str) -> tuple[str, tuple[int, ...]]:
    """Parse genomic resource ID with version.

    Genomic Resource Id Version Token is a Genomic Resource Id Token with
    an optional version appened. If present, the version suffix has the
    form "(3.3.2)". The default version is (0).
    Returns None if s in not a Genomic Resource Id Version. Otherwise
    returns token,version tupple
    """
    if token == "":
        return "", (0, )

    match = _GR_ID_WITH_VERSION_TOKEN_RE.fullmatch(token)
    if not match:
        raise ValueError(
            f"unexpected value for resource ID + version: {token}")
    token = match[1]
    version_string = match[2]
    if version_string:
        version = tuple(map(int, version_string.split(".")))
    else:
        version = (0,)
    return token, version


_RESOURCE_ID_WITH_VERSION_PATH_RE = re.compile(
    r"([a-zA-Z0-9/._-]+)(?:\(([1-9]\d*(?:\.\d+)*)\))?")


def parse_resource_id_version(
        resource_path: str) -> tuple[str, tuple[int, ...]]:
    """Parse genomic resource id and version path into Id, Version tuple.

    An optional version (0,) appened if needed. If present, the version suffix
    has the form "(3.3.2)". The default version is (0,).
    Returns tuple (None, None) if the path does not match the
    resource_id/version requirements. Otherwise returns tuple
    (resource_id, version).
    """
    if resource_path == "":
        return "", (0,)

    match = _RESOURCE_ID_WITH_VERSION_PATH_RE.fullmatch(resource_path)
    if not match:
        raise ValueError(f"unexpeced resource path: {resource_path}")
    token = match[1]
    version_string = match[2]
    if version_string:
        version = tuple(map(int, version_string.split(".")))
    else:
        version = (0,)
    return token, version


def version_string_to_suffix(version: str) -> str:
    """Transform version string into resource ID version suffix."""
    if version == "0":
        return ""
    return f"({version})"


def version_tuple_to_string(version: tuple[int, ...]) -> str:
    return ".".join(map(str, version))


def version_tuple_to_suffix(version: tuple[int, ...]) -> str:
    """Transform version tuple into resource ID version suffix."""
    if version == (0,):
        return ""
    return f"({'.'.join(map(str, version))})"


VERSION_CONSTRAINT_RE = re.compile(r"(>=|=)?(\d+(?:\.\d+)*)")


def is_version_constraint_satisfied(
        version_constraint: str | None, version: tuple[int, ...]) -> bool:
    """Check if a version matches a version constraint."""
    if not version_constraint:
        return True
    match = VERSION_CONSTRAINT_RE.fullmatch(version_constraint)
    if not match:
        raise ValueError(
            f"Bad syntax of version constraint {version_constraint}")
    operator = match[1] or ">="
    constraint_version = tuple(map(int, match[2].split(".")))
    if operator == "=":
        return version == constraint_version
    if operator == ">=":
        return version >= constraint_version
    raise ValueError(
        f"wrong operation {operator} in version constraint "
        f"{version_constraint}")


@dataclass(order=True)
class ManifestEntry:
    """Provides an entry into manifest object."""

    name: str
    size: int
    md5: str | None


@dataclass(order=True)
class ResourceFileState:
    """Defines resource file state saved into internal GRR state."""

    filename: str
    size: int
    timestamp: float
    md5: str


class Manifest:
    """Provides genomic resource manifest object."""

    def __init__(self) -> None:
        self.entries: dict[str, ManifestEntry] = {}

    @staticmethod
    def from_file_content(file_content: str) -> Manifest:
        """Produce a manifest from manifest file content."""
        manifest_entries = yaml.safe_load(file_content)
        if manifest_entries is None:
            manifest_entries = []
        return Manifest.from_manifest_entries(manifest_entries)

    @staticmethod
    def from_manifest_entries(
            manifest_entries: list[dict[str, Any]]) -> Manifest:
        """Produce a manifest from parsed manifest file content."""
        result = Manifest()
        for data in manifest_entries:
            entry = ManifestEntry(
                data["name"], data["size"], data["md5"])
            result.entries[entry.name] = entry
        return result

    def get_files(self) -> list[tuple[str, int]]:
        return [
            (entry.name, entry.size)
            for entry in self.entries.values()
        ]

    def __getitem__(self, name: str) -> ManifestEntry:
        return self.entries[name]

    def __contains__(self, name: str) -> bool:
        return name in self.entries

    def __iter__(self) -> Iterator[ManifestEntry]:
        return iter(sorted(self.entries.values()))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Manifest):
            return False
        return self.entries == other.entries

    def __len__(self) -> int:
        return len(self.entries)

    def __repr__(self) -> str:
        return str(self.entries)

    def to_manifest_entries(self) -> list[dict[str, Any]]:
        """Transform manifest to list of dictionaries.

        Helpfull when storing the manifest.
        """
        return [
            asdict(entry) for entry in sorted(self.entries.values())]

    def add(self, entry: ManifestEntry) -> None:
        """Add manifest enry to the manifest."""
        self.entries[entry.name] = entry

    def update(self, entries: dict[str, ManifestEntry]) -> None:
        for entry in entries.values():
            self.add(entry)

    def names(self) -> set[str]:
        """Return set of all file names from the manifest."""
        return set(self.entries.keys())


@dataclass
class ManifestUpdate:
    """Provides a manifest update object."""

    manifest: Manifest
    entries_to_delete: set[str]
    entries_to_update: set[str]

    def __bool__(self) -> bool:
        return bool(self.entries_to_delete or self.entries_to_update)


class GenomicResource:
    """Base class for genomic resources."""

    def __init__(
            self, resource_id: str, version: tuple[int, ...],
            protocol: RepositoryProtocol,
            config: dict[str, Any] | None = None,
            manifest: Manifest | None = None):

        self.resource_id = resource_id
        self.version: tuple[int, ...] = version
        self.config = config
        self.proto = protocol
        self._manifest: Manifest | None = manifest

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GenomicResource):
            return False
        return self.resource_id == other.resource_id and \
            self.version == other.version and \
            self.config == other.config and \
            self._manifest == other._manifest

    def __hash__(self) -> int:
        return hash(self.resource_id
                    + ".".join(map(str, self.version))
                    + self.proto.get_url())

    def invalidate(self) -> None:
        """Clean up cached attributes like manifest, etc."""
        self._manifest = None

    def get_id(self) -> str:
        """Return genomic resource ID."""
        return self.resource_id

    def get_full_id(self) -> str:
        """Return genomic resource ID with version."""
        version = ""
        if self.get_version_str() != "0":
            version = f"({self.get_version_str()})"
        return f"{self.resource_id}{version}"

    def get_config(self) -> dict[str, Any]:
        """Return the resouce configuration."""
        if self.config is None:
            raise ValueError(
                f"use of unconfigured genomic resource: {self.resource_id}")
        return self.config

    def get_description(self) -> str:
        """Return resource description."""
        config = self.get_config()
        if config is None:
            raise ValueError(f"resource {self.resource_id} not configured")
        if config.get("meta"):
            meta = config["meta"]
            if meta.get("description"):
                return str(meta["description"])
        return ""

    def get_summary(self) -> str | None:
        """Return resource summary."""
        config = self.get_config()
        if config is None:
            raise ValueError(f"resource {self.resource_id} not configured")
        if config.get("meta"):
            meta = config["meta"]
            if meta.get("summary"):
                return str(meta["summary"])
        return self.get_description()

    def get_repo_url(self) -> str:
        """Return repository's URL."""
        return self.proto.get_url()

    def get_url(self) -> str:
        return f"{self.get_repo_url()}/{self.get_full_id()}"

    def get_labels(self) -> dict[str, Any]:
        """Return resource labels."""
        config = self.get_config()
        if config is None:
            raise ValueError(f"resource {self.resource_id} not configured")
        if config.get("meta"):
            meta: dict[str, Any] = config["meta"]
            if meta.get("labels"):
                return cast(dict[str, Any], meta["labels"])
        return {}

    def get_type(self) -> str:
        """Return resource type as defined in 'genomic_resource.yaml'."""
        config = self.get_config()
        if config is None:
            raise ValueError(f"resource {self.resource_id} not configured")
        config_type = config.get("type")
        if config_type is None:
            return "Basic"
        return cast(str, config_type)

    def get_version_str(self) -> str:
        """Return version string of the form '3.1'."""
        return version_tuple_to_string(self.version)

    def get_genomic_resource_id_version(self) -> str:
        """Return a string combinint resource ID and version.

        Returns a string of the form aa/bb/cc[3.2] for a genomic resource with
        id aa/bb/cc and version 3.2.
        If the version is 0 the string will be aa/bb/cc.
        """
        return f"{self.resource_id}{version_tuple_to_suffix(self.version)}"

    def file_exists(self, filename: str) -> bool:
        """Check if filename exists in this resource."""
        return self.proto.file_exists(self, filename)

    def get_manifest(self) -> Manifest:
        """Load resource manifest if it exists. Otherwise builds it."""
        if self._manifest is None:
            self._manifest = self.proto.get_manifest(self)
        return self._manifest

    def get_file_url(self, filename: str) -> str:
        return self.proto.get_resource_file_url(self, filename)

    def get_file_content(
        self, filename: str,
        *,
        uncompress: bool = True,
        mode: str = "t",
    ) -> Any:
        """Return the content of file in a resource."""
        return self.proto.get_file_content(
            self, filename, uncompress=uncompress, mode=mode)

    def open_raw_file(
            self, filename: str, mode: str = "rt",
            **kwargs: str | bool | None) -> IO:
        """Open a file in the resource and returns a File-like object."""
        return self.proto.open_raw_file(
            self, filename, mode, **kwargs)

    def open_tabix_file(
            self, filename: str,
            index_filename: str | None = None) -> pysam.TabixFile:
        """Open a tabix file and returns a pysam.TabixFile."""
        return self.proto.open_tabix_file(self, filename, index_filename)

    def open_vcf_file(
            self, filename: str,
            index_filename: str | None = None) -> pysam.VariantFile:
        """Open a vcf file and returns a pysam.VariantFile."""
        return self.proto.open_vcf_file(self, filename, index_filename)

    def open_bigwig_file(self, filename: str) -> Any:
        """Open a bigwig file and return it."""
        return self.proto.open_bigwig_file(self, filename)


class Mode(enum.Enum):
    """Protocol mode."""

    READONLY = 1
    READWRITE = 2


class ReadOnlyRepositoryProtocol(abc.ABC):
    """Defines read only genomic resources repository protocol."""

    CHUNK_SIZE = 32768

    def __init__(self, proto_id: str, url: str):
        self.proto_id = proto_id
        self.url = url

    def mode(self) -> Mode:
        """Return repository protocol mode - READONLY or READWRITE."""
        return Mode.READONLY

    def get_id(self) -> str:
        """Return the repository ID."""
        return self.proto_id

    @abc.abstractmethod
    def get_url(self) -> str:
        """Return the repository URL."""

    @abc.abstractmethod
    def invalidate(self) -> None:
        """Invalidate internal cache of repository protocol."""

    @abc.abstractmethod
    def get_all_resources(self) -> Generator[GenomicResource, None, None]:
        """Return generator for all resources in the repository."""

    def find_resource(
        self, resource_id: str,
        version_constraint: str | None = None,
    ) -> GenomicResource | None:
        """Return requested resource or None if not found."""
        matching_resources: list[GenomicResource] = []
        for res in self.get_all_resources():
            if res.resource_id != resource_id:
                continue
            if is_version_constraint_satisfied(
                    version_constraint, res.version):
                matching_resources.append(res)
        if not matching_resources:
            return None

        def get_resource_version(res: GenomicResource) -> tuple[int, ...]:
            return res.version

        return max(
            matching_resources,
            key=get_resource_version)

    def get_resource(
            self, resource_id: str,
            version_constraint: str | None = None) -> GenomicResource:
        """Return requested resource or raises exception if not found.

        In case resource is not found a FileNotFoundError exception
        is raised.
        """
        resource = self.find_resource(resource_id, version_constraint)
        if resource is None:
            raise FileNotFoundError(
                f"resource <{resource_id}> ({version_constraint}) not found")
        return resource

    def load_yaml(self, resource: GenomicResource, filename: str) -> Any:
        """Return parsed YAML file."""
        content = self.get_file_content(
            resource, filename, uncompress=True)
        result = yaml.safe_load(content)
        if result is None:
            return {}
        return result

    def get_file_content(
        self, resource: GenomicResource,
        filename: str,
        *,
        uncompress: bool = True,
        mode: str = "t",
    ) -> Any:
        """Return content of a file in given resource."""
        with self.open_raw_file(
                resource, filename, mode=f"r{mode}",
                uncompress=uncompress) as infile:
            return infile.read()

    def get_resource_url(self, resource: GenomicResource) -> str:
        """Return url of the specified resources."""
        return os.path.join(
            self.url,
            resource.get_genomic_resource_id_version())

    def get_resource_file_url(
            self, resource: GenomicResource, filename: str) -> str:
        """Return url of a file in the resource."""
        return os.path.join(
            self.get_resource_url(resource), filename)

    @abc.abstractmethod
    def load_manifest(self, resource: GenomicResource) -> Manifest:
        """Load resource manifest."""

    @abc.abstractmethod
    def file_exists(self, resource: GenomicResource, filename: str) -> bool:
        """Check if given file exist in give resource."""

    @abc.abstractmethod
    def open_raw_file(
            self, resource: GenomicResource, filename: str,
            mode: str = "rt", **kwargs: str | bool | None) -> IO:
        """Open file in a resource and returns a file-like object."""

    @abc.abstractmethod
    def open_tabix_file(
            self, resource: GenomicResource, filename: str,
            index_filename: str | None = None) -> pysam.TabixFile:
        """Open a tabix file in a resource and return a pysam tabix file.

        Not all repositories support this method. Repositories that do
        no support this method raise and exception.
        """

    @abc.abstractmethod
    def open_vcf_file(
            self, resource: GenomicResource, filename: str,
            index_filename: str | None = None) -> pysam.VariantFile:
        """Open a vcf file in a resource and return a pysam VariantFile.

        Not all repositories support this method. Repositories that do
        no support this method raise and exception.
        """

    @abc.abstractmethod
    def open_bigwig_file(
        self, resource: GenomicResource, filename: str,
    ) -> Any:
        """Open a bigwig file in a resource and return it.

        Not all repositories support this method. Repositories that do
        no support this method raise and exception.
        """

    def compute_md5_sum(self, resource: GenomicResource, filename: str) -> str:
        """Compute a md5 hash for a file in the resource."""
        logger.debug(
            "compute md5sum for %s in %s", filename, resource.resource_id)

        with self.open_raw_file(resource, filename, "rb") as infile:
            md5_hash = hashlib.md5()  # noqa S324
            while chunk := infile.read(self.CHUNK_SIZE):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()

    def get_manifest(self, resource: GenomicResource) -> Manifest:
        """Load and returns a resource manifest."""
        return self.load_manifest(resource)

    def build_genomic_resource(
            self, resource_id: str, version: tuple[int, ...],
            config: dict | None = None,
            manifest: Manifest | None = None) -> GenomicResource:
        """Build a genomic resource based on this protocol."""
        if not config:
            res = GenomicResource(resource_id, version, self)
            config = self.load_yaml(res, GR_CONF_FILE_NAME)

        return GenomicResource(
            resource_id, version, self, config, manifest)


class ReadWriteRepositoryProtocol(ReadOnlyRepositoryProtocol):
    """Defines read write genomic resources repository protocol."""

    # pylint: disable=too-many-public-methods

    def mode(self) -> Mode:
        return Mode.READWRITE

    @abc.abstractmethod
    def collect_all_resources(self) -> Generator[GenomicResource, None, None]:
        """Return generator for all resources managed by this protocol."""

    @abc.abstractmethod
    def collect_resource_entries(self, resource: GenomicResource) -> Manifest:
        """Scan the resource and returns manifest with all files."""

    def _update_manifest_entry_and_state(
            self, resource: GenomicResource, entry: ManifestEntry,
            prebuild_entries: dict[str, ManifestEntry]) -> None:
        pre_state = self.load_resource_file_state(resource, entry.name)
        size = None
        md5 = None
        if entry.name in prebuild_entries:
            ready_entry = prebuild_entries[entry.name]
            size = ready_entry.size
            md5 = ready_entry.md5

        if pre_state is None:
            state = self.build_resource_file_state(
                resource, entry.name, size=size, md5=md5)
            self.save_resource_file_state(resource, state)
        elif entry.name in prebuild_entries:
            state = self.build_resource_file_state(
                resource, entry.name, size=size, md5=md5)
        else:
            timestamp = self.get_resource_file_timestamp(resource, entry.name)
            size = self.get_resource_file_size(resource, entry.name)
            if timestamp == pre_state.timestamp and size == pre_state.size:
                state = pre_state
            else:
                state = self.build_resource_file_state(
                    resource, entry.name, size=size, md5=md5)
                self.save_resource_file_state(resource, state)

        entry.md5 = state.md5
        entry.size = state.size

    def build_manifest(
        self, resource: GenomicResource,
        prebuild_entries: dict[str, ManifestEntry] | None = None,
    ) -> Manifest:
        """Build full manifest for the resource."""
        if prebuild_entries is None:
            prebuild_entries = {}

        manifest = Manifest()
        for entry in self.collect_resource_entries(resource):
            self._update_manifest_entry_and_state(
                resource, entry, prebuild_entries)
            manifest.add(entry)
        return manifest

    def check_update_manifest(
        self, resource: GenomicResource,
        prebuild_entries: dict[str, ManifestEntry] | None = None,
    ) -> ManifestUpdate:
        """Check if the resource manifest needs update."""
        try:
            current_manifest = self.load_manifest(resource)
        except FileNotFoundError:
            current_manifest = Manifest()

        manifest = Manifest()
        entries_to_update = set()
        for entry in self.collect_resource_entries(resource):
            manifest.add(entry)
            state = self.load_resource_file_state(resource, entry.name)
            if state is None:
                md5 = None
                size = None
                if prebuild_entries and entry.name in prebuild_entries:
                    md5 = prebuild_entries[entry.name].md5
                    size = prebuild_entries[entry.name].size
                state = self.build_resource_file_state(
                    resource, entry.name,
                    md5=md5, size=size)
                self.save_resource_file_state(resource, state)
            if state.filename not in current_manifest:
                entries_to_update.add(entry.name)
                continue
            file_timestamp = self.get_resource_file_timestamp(
                resource, entry.name)
            file_size = self.get_resource_file_size(
                resource, entry.name)
            if state.timestamp != file_timestamp or \
                    state.size != file_size:
                md5 = None
                if prebuild_entries and entry.name in prebuild_entries:
                    md5 = prebuild_entries[entry.name].md5
                state = self.build_resource_file_state(
                    resource, entry.name, md5=md5)
                if state.md5 == current_manifest[entry.name].md5:
                    self.save_resource_file_state(resource, state)
                else:
                    entries_to_update.add(entry.name)
                continue
            if state.md5 != current_manifest[entry.name].md5:
                entries_to_update.add(entry.name)
                continue

            entry.md5 = state.md5
            entry.size = state.size

        if prebuild_entries is not None:
            manifest.update(prebuild_entries)

        entries_to_delete = current_manifest.names() - manifest.names()
        return ManifestUpdate(manifest, entries_to_delete, entries_to_update)

    def update_manifest(
        self, resource: GenomicResource,
        prebuild_entries: dict[str, ManifestEntry] | None = None,
    ) -> Manifest:
        """Update or create full manifest for the resource."""
        manifest_update = self.check_update_manifest(
            resource, prebuild_entries)

        if not bool(manifest_update):
            return manifest_update.manifest

        manifest = manifest_update.manifest
        if prebuild_entries is None:
            prebuild_entries = {}

        for filename in manifest_update.entries_to_update:
            entry = manifest[filename]
            self._update_manifest_entry_and_state(
                resource, entry, prebuild_entries)

        return manifest

    def save_manifest(
            self, resource: GenomicResource, manifest: Manifest) -> None:
        """Save manifest into genomic resource's directory."""
        logger.debug(
            "save manifest of resource %s from %s", resource.resource_id,
            self.proto_id)

        with self.open_raw_file(
                resource, GR_MANIFEST_FILE_NAME, "wt") as outfile:
            yaml.dump(manifest.to_manifest_entries(), outfile)
        resource.invalidate()

    def save_index(self, resource: GenomicResource, contents: str) -> None:
        """Save an index HTML file into the genomic resource's directory."""
        with self.open_raw_file(resource, GR_INDEX_FILE_NAME, "wt") as outfile:
            outfile.write(contents)

    def get_manifest(self, resource: GenomicResource) -> Manifest:
        """Load or build a resource manifest."""
        try:
            manifest = self.load_manifest(resource)
        except FileNotFoundError:
            manifest = self.build_manifest(resource)
        return manifest

    @abc.abstractmethod
    def get_resource_file_timestamp(
            self, resource: GenomicResource, filename: str) -> float:
        """Return the timestamp (ISO formatted) of a resource file."""

    @abc.abstractmethod
    def get_resource_file_size(
            self, resource: GenomicResource, filename: str) -> int:
        """Return the size of a resource file."""

    def build_resource_file_state(
            self, resource: GenomicResource,
            filename: str,
            **kwargs: str | float | int | None) -> ResourceFileState:
        """Build resource file state."""
        if not self.file_exists(resource, filename):
            raise ValueError(
                f"can't build resource state for not existing resource file "
                f"{resource.resource_id} > {filename}")

        md5 = kwargs.get("md5")
        timestamp = kwargs.get("timestamp")
        size = kwargs.get("size")

        if md5 is None:
            md5 = self.compute_md5_sum(resource, filename)

        if timestamp is None:
            timestamp = self.get_resource_file_timestamp(resource, filename)

        if size is None:
            size = self.get_resource_file_size(resource, filename)

        return ResourceFileState(
            filename,
            cast(int, size),
            cast(float, timestamp),
            cast(str, md5))

    @abc.abstractmethod
    def save_resource_file_state(
            self, resource: GenomicResource, state: ResourceFileState) -> None:
        """Save resource file state into internal GRR state."""

    @abc.abstractmethod
    def load_resource_file_state(
            self, resource: GenomicResource,
            filename: str) -> ResourceFileState | None:
        """Load resource file state from internal GRR state.

        If the specified resource file has no internal state returns None.
        """

    @abc.abstractmethod
    def delete_resource_file(
            self, resource: GenomicResource, filename: str) -> None:
        """Delete a resource file and it's internal state."""

    @abc.abstractmethod
    def copy_resource_file(
            self,
            remote_resource: GenomicResource,
            dest_resource: GenomicResource,
            filename: str) -> ResourceFileState | None:
        """Copy a remote resource file into local repository."""

    @abc.abstractmethod
    def update_resource_file(
            self, remote_resource: GenomicResource,
            dest_resource: GenomicResource,
            filename: str) -> ResourceFileState | None:
        """Update a resource file into repository if needed."""

    def get_or_create_resource(
            self, resource_id: str,
            version: tuple[int, ...]) -> GenomicResource:
        """Return a resource with specified ID and version.

        If the resource is not found create an empty resource.
        """
        resource = self.find_resource(
            resource_id=resource_id,
            version_constraint=f"={version_tuple_to_string(version)}")

        if resource is None:
            logger.info(
                "resource %s (%s) not found in %s; creating...",
                resource_id,
                version,
                self.get_id())
            resource = GenomicResource(
                resource_id,
                version,
                self)

        return resource

    def copy_resource(
            self,
            remote_resource: GenomicResource) -> GenomicResource:
        """Copy a remote resource into repository."""
        local_resource = self.get_or_create_resource(
            remote_resource.resource_id, remote_resource.version)

        remote_manifest = remote_resource.get_manifest()
        local_manifest = self.get_manifest(local_resource)
        filenames_to_delete = local_manifest.names() - remote_manifest.names()

        for filename in filenames_to_delete:
            self.delete_resource_file(local_resource, filename)

        for manifest_entry in remote_manifest:
            self.copy_resource_file(
                remote_resource, local_resource, manifest_entry.name)

        self.save_manifest(local_resource, remote_resource.get_manifest())
        self.invalidate()

        return self.get_resource(
            resource_id=remote_resource.resource_id,
            version_constraint=f"={remote_resource.get_version_str()}")

    def update_resource(
        self,
        remote_resource: GenomicResource,
        files_to_copy: set[str] | None = None,
    ) -> GenomicResource:
        """Copy a remote resource into repository.

        Allows copying of a subset of files from the resource via
        files_to_copy. If files_to_copy is None, copies all files.
        """
        local_resource = self.get_or_create_resource(
            remote_resource.resource_id, remote_resource.version)
        remote_manifest = remote_resource.get_manifest()
        local_manifest = self.get_manifest(local_resource)
        filenames_to_delete = local_manifest.names() - remote_manifest.names()

        if files_to_copy is None:
            files_to_copy = {entry.name for entry in remote_manifest}
        else:
            files_to_copy.add(GR_CONF_FILE_NAME)  # config is always required

        for filename in filenames_to_delete:
            self.delete_resource_file(local_resource, filename)
        for file in files_to_copy:
            self.update_resource_file(remote_resource, local_resource, file)

        if local_manifest != remote_manifest:
            self.save_manifest(local_resource, remote_resource.get_manifest())
            self.invalidate()

        return self.get_resource(
            resource_id=remote_resource.resource_id,
            version_constraint=f"={remote_resource.get_version_str()}")

    @abc.abstractmethod
    def build_content_file(self) -> list[dict[str, Any]]:
        """Build the content of the repository (i.e '.CONTENTS.json' file)."""


class GenomicResourceRepo(abc.ABC):
    """Base class for genomic resources repositories."""

    def __init__(self, repo_id: str):
        self._repo_id: str = repo_id
        self._definition: dict[str, Any] | None = None

    @property
    def definition(self) -> dict[str, Any] | None:
        if self._definition:
            return copy.deepcopy(self._definition)
        return self._definition

    @definition.setter
    def definition(self, value: dict[str, Any]) -> None:
        self._definition = copy.deepcopy(value)

    @abc.abstractmethod
    def invalidate(self) -> None:
        """Invalidate internal state of the repository."""

    @property
    def repo_id(self) -> str:
        return self._repo_id

    @abc.abstractmethod
    def get_resource(
            self, resource_id: str, version_constraint: str | None = None,
            repository_id: str | None = None) -> GenomicResource:
        """Return one resource with id qual to resource_id.

        If resource is not found, exception is raised.
        """

    @abc.abstractmethod
    def find_resource(
            self, resource_id: str, version_constraint: str | None = None,
            repository_id: str | None = None) -> GenomicResource | None:
        """Return one resource with id qual to resource_id.

        If resource is not found, None is returned.
        """

    @abc.abstractmethod
    def get_all_resources(self) -> Generator[GenomicResource, None, None]:
        """Return a generator over all resource in the repository."""


class GenomicResourceProtocolRepo(GenomicResourceRepo):
    """Base class for real genomic resources repositories."""

    def __init__(
            self,
            proto: ReadOnlyRepositoryProtocol | ReadWriteRepositoryProtocol):
        super().__init__(proto.get_id())
        self.proto = proto

    def invalidate(self) -> None:
        self.proto.invalidate()

    def get_resource(
            self, resource_id: str, version_constraint: str | None = None,
            repository_id: str | None = None) -> GenomicResource:

        if repository_id and self.repo_id != repository_id:
            raise ValueError(
                f"can't find resource ({resource_id}, {version_constraint}: "
                f"repository {repository_id} in repository {self.repo_id}")

        return self.proto.get_resource(resource_id, version_constraint)

    def find_resource(
            self, resource_id: str, version_constraint: str | None = None,
            repository_id: str | None = None) -> GenomicResource | None:

        if repository_id and self.repo_id != repository_id:
            return None

        return self.proto.find_resource(resource_id, version_constraint)

    def get_all_resources(self) -> Generator[GenomicResource, None, None]:
        return self.proto.get_all_resources()


RepositoryProtocol = ReadOnlyRepositoryProtocol | ReadWriteRepositoryProtocol
