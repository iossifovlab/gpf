"""Provides basic classes for genomic resources and repositories."""
from __future__ import annotations

import re
import logging
import datetime
import enum
from typing import List, Optional, cast, Tuple, Dict, Any
from dataclasses import dataclass, asdict, field

import abc
import yaml

logger = logging.getLogger(__name__)


GR_CONF_FILE_NAME = "genomic_resource.yaml"
GR_MANIFEST_FILE_NAME = ".MANIFEST"
GRP_CONTENTS_FILE_NAME = ".CONTENTS"

GR_ENCODING = "utf-8"

_GR_ID_TOKEN_RE = re.compile("[a-zA-Z0-9._-]+")


def is_gr_id_token(token):
    """
    Genomic Resource Id Token is a string with one or more letters,
    numbers, '.', '_', or '-'. The function checks if the parameter
    token is a Genomic REsource Id Token.
    """
    return bool(_GR_ID_TOKEN_RE.fullmatch(token))


_GR_ID_WITH_VERSION_TOKEN_RE = re.compile(
    r"([a-zA-Z0-9._-]+)(?:\[([1-9]\d*(?:\.\d+)*)\])?")


def parse_gr_id_version_token(token):
    """
    Genomic Resource Id Version Token is a Genomic Resource Id Token with
    an optional version appened. If present, the version suffix has the
    form "[3.3.2]". The default version is [0].
    Returns None if s in not a Genomic Resource Id Version. Otherwise
    returns token,version tupple
    """
    match = _GR_ID_WITH_VERSION_TOKEN_RE.fullmatch(token)
    if not match:
        return None
    token = match[1]
    version_string = match[2]
    if version_string:
        version = tuple(map(int, version_string.split(".")))
    else:
        version = (0,)
    return token, version


def version_tuple_to_suffix(version):
    """Transforms version token into string."""
    if version == (0,):
        return ""
    return "[" + ".".join(map(str, version)) + "]"


VERSION_CONSTRAINT_RE = re.compile(r"(>=|=)?(\d+(?:\.\d+)*)")


def is_version_constraint_satisfied(version_constraint, version):
    """Checks if a version matches a version constraint."""
    if not version_constraint:
        return True
    match = VERSION_CONSTRAINT_RE.fullmatch(version_constraint)
    if not match:
        raise ValueError(
            f'Bad sintax of version constraint {version_constraint}')
    operator = match[1] if match[1] else ">="
    constraint_version = tuple(map(int, match[2].split(".")))
    if operator == "=":
        return version == constraint_version
    if operator == ">=":
        return version >= constraint_version
    raise ValueError(
        f"wrong operation {operator} in version constraint "
        f"{version_constraint}")


def find_genomic_resource_files_helper(
        content_dict, leaf_to_size_and_date, prev=None):
    """
    Helper function to iterate over directory yielding
    (filename, size, timestamp) for each file in directory and its
    subdirectories.
    """

    if prev is None:
        prev = []

    for name, content in content_dict.items():
        if name[0] == ".":
            continue
        nxt = prev + [name]
        if isinstance(content, dict):
            yield from find_genomic_resource_files_helper(
                content, leaf_to_size_and_date, nxt)
        else:
            fsize, ftimestamp = leaf_to_size_and_date(content)
            yield "/".join(nxt), fsize, ftimestamp


def _scan_content_dict_for_genomic_resources(content_dict, parent_id):  # NOSONAR
    resources_counter = 0
    unused_dirs = set([])

    for name, content in content_dict.items():
        id_ver = parse_gr_id_version_token(name)
        if isinstance(content, dict) and id_ver and \
                GR_CONF_FILE_NAME in content and \
                not isinstance(content[GR_CONF_FILE_NAME], dict):
            # resource found
            resource_id, version = id_ver
            yield "/".join(parent_id + [resource_id]), version
            resources_counter += 1
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
            dir_resource_counter = 0
            for resource_id, version in _scan_content_dict_for_genomic_resources(
                    content, curr_id):
                yield resource_id, version
                resources_counter += 1
                dir_resource_counter += 1
            if dir_resource_counter == 0:
                unused_dirs.add(curr_id_path)
    if resources_counter > 0:
        for dir_id in unused_dirs:
            logger.warning("directory <%s> contains no resources.", dir_id)


def find_genomic_resources_helper(content_dict, parent_id=None):
    """
    Helper function to iterate over directory and its subdirectories
    yielding (resource_id, version) for each resource found.
    """
    if GR_CONF_FILE_NAME in content_dict and \
            not isinstance(content_dict[GR_CONF_FILE_NAME], dict):
        yield "", (0,)
        return

    if parent_id is None:
        parent_id = []

    yield from _scan_content_dict_for_genomic_resources(
        content_dict, parent_id)

@dataclass(order=True)
class ManifestEntry:
    """Provides an entry into manifest object"""
    name: str
    size: int
    time: str = field(compare=False)
    md5: Optional[str] = field(compare=False)

    def get_timestamp(self) -> int:
        """Returns UNIX timestamp corresponding to entry time."""
        return int(datetime.datetime.fromisoformat(
            self.time).timestamp())

    @staticmethod
    def convert_timestamp(timestamp: float):
        """Produces ISO formatted date-time from python time.time().

        Uses integer precicsion, i.e. the timestamp is converted to int.
        """
        return datetime.datetime.fromtimestamp(
                int(timestamp), datetime.timezone.utc).isoformat()

class Manifest:
    """Provides genomic resource manifest object."""
    def __init__(self):
        self.entries: Dict[str, ManifestEntry] = {}

    @staticmethod
    def from_file_content(file_content: str) -> Manifest:
        """Produces a manifest from manifest file content."""
        manifest_entries = yaml.safe_load(file_content)
        return Manifest.from_manifest_entries(manifest_entries)

    @staticmethod
    def from_manifest_entries(
            manifest_entries: List[Dict[str, Any]]) -> Manifest:
        """Produces a manifest from parsed manifest file content."""

        result = Manifest()
        for data in manifest_entries:
            entry = ManifestEntry(
                data["name"], data["size"], data["time"], data["md5"])
            result.entries[entry.name] = entry
        return result

    def get_files(self):
        return [
            (entry.name, entry.size, entry.time)
            for entry in self.entries.values()
        ]

    def __getitem__(self, name):
        return self.entries[name]

    def __contains__(self, name):
        return name in self.entries

    def __iter__(self):
        return iter(self.entries.values())

    def __eq__(self, other):
        if not isinstance(other, Manifest):
            return False
        if len(self.entries) != len(other.entries):
            return False

        for name, entry in self.entries.items():
            if name not in other:
                return False
            other_entry = other[name]
            if entry != other_entry:
                return False

        return True

    def __repr__(self):
        return str(self.entries)

    def to_manifest_entries(self):
        """Transforms manifest to list of dictionaries.

        Helpfull when storing the manifest."""
        return [
            asdict(entry) for entry in self.entries.values()]

    def add(self, entry: ManifestEntry) -> None:
        """Adds manifest enry to the manifest."""
        self.entries[entry.name] = entry


class GenomicResource:
    """Base class for genomic resources."""
    def __init__(self, resource_id, version, repo: GenomicResourceRealRepo,
                 config=None):
        self.resource_id = resource_id
        self.version = version
        self.config = config
        self.repo = repo
        self._manifest: Optional[Manifest] = None

    def refresh(self):
        """Clean up cached attributes like manifest, etc."""
        self._manifest = None

    def get_id(self):
        """Returns genomic resource ID."""
        return self.resource_id

    def get_config(self):
        """Returns the resouce configuration."""
        return self.config

    def get_type(self):
        """Returns resource type ad defined in 'genomic_resource.yaml'."""
        config_type = self.get_config().get("type")
        if config_type is None:
            return "Basic"
        return config_type

    def get_version_str(self) -> str:
        """returns string of the form 3.1"""
        return ".".join(map(str, self.version))

    def get_genomic_resource_id_version(self) -> str:
        """
        returns a string of the form aa/bb/cc[3.2] for a genomic resource with
        id aa/bb/cc and version 3.2.
        If the version is 0 the string will be aa/bb/cc.
        """
        return f"{self.resource_id}{version_tuple_to_suffix(self.version)}"

    # def get_files(self) -> List[Tuple[str, int, str]]:
    #     """
    #     Returns a list of tuples (filename,filesize,filetime) for each of
    #     the files in the genomic resource.
    #     Files and directories staring with "." are ignored.
    #     """
    #     return self.repo.get_files(self)

    def file_exists(self, filename):
        """
        Returns whether filename exists in this resource
        """
        return self.repo.file_exists(self, filename)

    def file_local(self, filename):
        """
        Returns whether filename can be accessed locally in this resource
        """
        return self.repo.file_local(self, filename)

    def get_manifest(self) -> Manifest:
        """Loads resource manifest if it exists. Otherwise builds it."""
        if self._manifest is None:
            self._manifest = self.repo.get_manifest(self)
        assert isinstance(self._manifest, Manifest), self._manifest
        return self._manifest

    def get_file_content(self, filename, uncompress=True, mode="t"):
        """Returns the content of file in a resource."""
        return self.repo.get_file_content(
            self, filename, uncompress=uncompress, mode=mode)

    def open_raw_file(
            self, filename, mode="rt", uncompress=False, seekable=False):
        """Opens a file in the resource and returns a File-like object."""
        return self.repo.open_raw_file(
            self, filename, mode, uncompress, seekable)

    def open_tabix_file(self, filename, index_filename=None):
        """Opens a tabix file and returns a pysam.TabixFile."""
        return self.repo.open_tabix_file(self, filename, index_filename)


class Mode(enum.Enum):
    """Protocol mode."""

    READONLY = 1
    READWRITE = 2


class RepositoryProtocol(abc.ABC):
    """Read only genomic resources repository protocol."""

    def __init__(self, proto_id: str):
        self.proto_id = proto_id

    @abc.abstractmethod
    def mode(self):
        """Returns protocol model."""

    def get_id(self):
        """Returns the repository ID."""
        return self.proto_id

    def load_yaml(self, genomic_resource, filename):
        """Returns parsed YAML file."""

        content = self.get_file_content(
            genomic_resource, filename, uncompress=True)
        return yaml.safe_load(content)

    def get_file_content(
            self, resource, filename, uncompress=True, mode="t"):
        """Returns content of a file in given resource"""
        with self.open_raw_file(
                resource, filename, mode=f"r{mode}",
                uncompress=uncompress) as infile:
            return infile.read()

    def get_manifest(self, resource):
        """Loads resource manifest."""
        content = self.get_file_content(resource, GR_MANIFEST_FILE_NAME)
        return Manifest.from_file_content(content)

    @abc.abstractmethod
    def file_exists(self, resource, filename) -> bool:
        """Check if given file exist in give resource"""

    @abc.abstractmethod
    def open_raw_file(
            self, resource, filename,
            mode="rt", **kwargs):
        """Opens file in a resource and returns a file-like object"""

    @abc.abstractmethod
    def open_tabix_file(
            self, resource,  filename, index_filename=None):
        """
        Open a tabix file in a resource and return a pysam tabix file object.

        Not all repositories support this method. Repositories that do
        no support this method raise and exception.
        """

    def build_genomic_resource(
            self, resource_id, version, config=None,
            manifest: Optional[Manifest] = None):

        """Builds a genomic resource based on this protocol."""
        if not config:
            res = GenomicResource(resource_id, version, self)
            config = self.load_yaml(res, GR_CONF_FILE_NAME)

        resource = GenomicResource(resource_id, version, self, config)
        resource._manifest = manifest  # pylint: disable=protected-access
        return resource


class ReadOnlyRepositoryProtocol(RepositoryProtocol):

    def mode(self):
        return Mode.READWRITE

class ReadWriteRepositoryProtocol(RepositoryProtocol):

    def mode(self):
        return Mode.READWRITE


class GenomicResourceRepo(abc.ABC):
    """Base class for genomic resources repositories."""

    def __init__(self, repo_id):
        self.repo_id: str = repo_id

    @abc.abstractmethod
    def get_resource(self, resource_id, version_constraint=None,
                     genomic_repository_id=None) -> Optional[GenomicResource]:
        """
        Returns one resource with id qual to resource_id. If not found,
        None is returned.
        """

    @abc.abstractmethod
    def get_all_resources(self) -> List[GenomicResource]:
        """
        Returns a list of GenomicResource objects stored in the repository.
        """


class GenomicResourceRealRepo(GenomicResourceRepo):
    """Base class for real genomic resources repositories."""

    def build_genomic_resource(
            self, resource_id, version, config=None,
            manifest: Optional[Manifest] = None):
        """Builds a genomic resource belonging to this repository."""
        if not config:
            res = GenomicResource(resource_id, version, self)
            config = self.load_yaml(res, GR_CONF_FILE_NAME)

        resource = GenomicResource(resource_id, version, self, config)
        resource._manifest = manifest  # pylint: disable=protected-access
        return resource

    def get_resource(self, resource_id, version_constraint=None,
                     genomic_repository_id=None) -> Optional[GenomicResource]:

        if genomic_repository_id and self.repo_id != genomic_repository_id:
            return None

        matching_resources = []
        for res in self.get_all_resources():
            if res.resource_id != resource_id:
                continue
            if is_version_constraint_satisfied(
                    version_constraint, res.version):
                matching_resources.append(res)
        if not matching_resources:
            return None
        return cast(
            GenomicResource,
            max(matching_resources, key=lambda x: x.version))  # type: ignore

    def load_yaml(self, genomic_resource, filename):
        """Returns parsed YAML file."""

        content = self.get_file_content(
            genomic_resource, filename, uncompress=True)
        return yaml.safe_load(content)

    def get_file_content(
            self, resource, filename, uncompress=True, mode="t"):
        """Returns content of a file in given resource"""
        with self.open_raw_file(
                resource, filename, mode=f"r{mode}",
                uncompress=uncompress) as infile:
            return infile.read()

    def get_manifest(self, resource):
        """Loads resource manifest."""
        content = self.get_file_content(resource, GR_MANIFEST_FILE_NAME)
        return Manifest.from_file_content(content)

    # @abc.abstractmethod
    # def get_files(self, resource) -> List[Tuple[str, int, str]]:
    #     """Returns a list of files for given resource.

    #     For each file in the resource returns a tuple, containing the
    #     file name, file size and file timestamp.
    #     """

    @abc.abstractmethod
    def file_exists(self, resource, filename) -> bool:
        """Check if given file exist in give resource"""

    def file_local(self, genomic_resource, filename):
        """Check if a given file in a given resource can be accessed locally"""
        return False

    @abc.abstractmethod
    def open_raw_file(
            self, resource, filename,
            mode="rt", uncompress=False, seekable=False):
        """Opens file in a resource and returns a file-like object"""

    @abc.abstractmethod
    def open_tabix_file(
            self, resource,  filename, index_filename=None):
        """
        Open a tabix file in a resource and return a pysam tabix file object.

        Not all repositories support this method. Repositories that do
        no support this method raise and exception.
        """
