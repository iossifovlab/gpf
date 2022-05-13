from __future__ import annotations

import re
import logging
from typing import List, Optional, cast, Tuple, Dict, Any, Union
from dataclasses import dataclass, asdict

import abc
import hashlib
import yaml

logger = logging.getLogger(__name__)


GR_CONF_FILE_NAME = "genomic_resource.yaml"
GR_MANIFEST_FILE_NAME = ".MANIFEST"
GRP_CONTENTS_FILE_NAME = ".CONTENTS"

GR_ENCODING = 'utf-8'

_GR_ID_TOKEN_RE = re.compile('[a-zA-Z0-9._-]+')


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
    if version == (0,):
        return ""
    return "[" + ".".join(map(str, version)) + "]"


VERSION_CONSTRAINT_RE = re.compile(r"(>=|=)?(\d+(?:\.\d+)*)")


def is_version_constraint_satisfied(version_constraint, version):
    if not version_constraint:
        return True
    match = VERSION_CONSTRAINT_RE.fullmatch(version_constraint)
    if not match:
        raise ValueError(f'Wrong version constrainted {version_constraint}')
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
        prev= []

    for name, content in content_dict.items():
        if name[0] == ".":
            continue
        nxt = prev+ [name]
        if isinstance(content, dict):
            yield from find_genomic_resource_files_helper(
                content, leaf_to_size_and_date, nxt)
        else:
            fsize, ftimestamp = leaf_to_size_and_date(content)
            yield "/".join(nxt), fsize, ftimestamp


def find_genomic_resources_helper(content_dict, id_prev=None):
    """
    Helper function to iterate over directory and its subdirectories
    yielding (resource_id, version) for each resource found.
    """
    if id_prev is None:
        id_prev = []

    resources_counter = 0
    unused_dirs = set([])
    if GR_CONF_FILE_NAME in content_dict and \
            not isinstance(content_dict[GR_CONF_FILE_NAME], dict):
        yield "", (0,)
        return
    for name, content in content_dict.items():
        if name[0] == '.':
            continue
        idvr = parse_gr_id_version_token(name)
        if isinstance(content, dict) and idvr and \
                GR_CONF_FILE_NAME in content and \
                not isinstance(content[GR_CONF_FILE_NAME], dict):
            resource_id, version = idvr
            yield "/".join(id_prev + [resource_id]), version
            resources_counter += 1
        else:
            curr_id = id_prev + [name]
            curr_id_path = "/".join(curr_id)
            if not isinstance(content, dict):
                logger.warning("The file %s is not used.", curr_id_path)
                continue
            if not is_gr_id_token(name):
                logger.warning(
                    "The directory %s has a name %s that is not a "
                    "valid Genomic Resoruce Id Token.", curr_id_path, name)
                continue
            dir_resource_counter = 0
            for resource_id, version in find_genomic_resources_helper(content, curr_id):
                yield resource_id, version
                resources_counter += 1
                dir_resource_counter += 1
            if dir_resource_counter == 0:
                unused_dirs.add(curr_id_path)
    if resources_counter > 0:
        for dir_id in unused_dirs:
            logger.warning("The directory %s contains no resources.", dir_id)


@dataclass
class ManifestEntry:
    """Provides an entry into manifest object"""
    name: str
    size: int
    time: str
    md5: Optional[str]


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

    def get_genomic_resource_dir(self) -> str:
        """
        returns a string of the form aa/bb/cc[3.2] for a genomic resource with
        id aa/bb/cc and version 3.2.
        If the version is 0 the string will be aa/bb/cc.
        """
        return f"{self.resource_id}{version_tuple_to_suffix(self.version)}"

    def get_files(self) -> List[Tuple[str, int, str]]:
        """
        Returns a generator returning (filename,filesize,filetime) for each of
        the files in the genomic resource.
        Files and directories staring with "." are ignored.
        """
        return self.repo.get_files(self)

    def file_exists(self, filename):
        """
        Returns whether filename exists in this resource
        """
        return self.repo.file_exists(self, filename)

    def compute_md5_sum(self, filename):
        """Computes a md5 hash for a file in the resource"""

        with self.open_raw_file(filename, "rb") as infile:
            md5_hash = hashlib.md5()
            while d := infile.read(8192):
                md5_hash.update(d)
        return md5_hash.hexdigest()

    def build_manifest(self):
        """Builds full manifest for the resource"""

        return Manifest.from_manifest_entries(
            [
                {
                    "name": fn,
                    "size": fs,
                    "time": ft,
                    "md5": self.compute_md5_sum(fn)
                }
                for fn, fs, ft in sorted(self.get_files())])

    def update_manifest(self):
        """Updates resource manifest and stores it."""
        try:
            current_manifest = self.load_manifest()
            new_manifest_entries = []
            for fname, fsize, ftime in sorted(self.get_files()):
                md5 = None
                if fname in current_manifest:
                    entry = current_manifest[fname]
                    if entry["size"] == fsize and entry["time"] == ftime:
                        md5 = entry["md5"]
                    else:
                        logger.debug(
                            "md5 sum for file %s for resource %s needs update",
                            fname, self.resource_id)
                else:
                    logger.debug(
                        "found a new file %s for resource %s",
                        fname, self.resource_id)
                if not md5:
                    md5 = self.compute_md5_sum(fname)
                new_manifest_entries.append(
                    {"name": fname, "size": fsize, "time": ftime, "md5": md5})

            new_manifest = Manifest.from_manifest_entries(new_manifest_entries)
            if new_manifest != current_manifest:
                self.save_manifest(new_manifest)
        except Exception:
            logger.info(
                "building a new manifest for resource %s", self.resource_id,
                exc_info=True)
            manifest = self.build_manifest()
            self.save_manifest(manifest)

    def load_manifest(self) -> Manifest:
        """Loads resource manifest"""
        return Manifest.from_manifest_entries(
            self.load_yaml(GR_MANIFEST_FILE_NAME))

    def save_manifest(self, manifest: Manifest):
        """Saves manifest into genomic resources directory."""
        with self.open_raw_file(GR_MANIFEST_FILE_NAME, "wt") as outfile:
            yaml.dump(manifest.to_manifest_entries(), outfile)
        self._manifest = manifest

    def get_manifest(self) -> Manifest:
        """Loads resource manifest if it exists. Otherwise builds it."""
        if self._manifest is None:
            try:
                self._manifest = self.load_manifest()
                logger.debug("manifest loaded: %s", self._manifest)
            except FileNotFoundError:
                self._manifest = self.build_manifest()
                logger.debug("manifest builded: %s", self._manifest)
        assert isinstance(self._manifest, Manifest), self._manifest
        return self._manifest

    def load_yaml(self, filename):
        """Loads a yaml file and returns its parsed content"""
        return self.repo.load_yaml(self, filename)

    def get_file_content(self, filename, uncompress=True, mode="t"):
        return self.repo.get_file_content(
            self, filename, uncompress=uncompress, mode=mode)

    def open_raw_file(
            self, filename, mode="rt", uncompress=False, seekable=False):
        return self.repo.open_raw_file(
            self, filename, mode, uncompress, seekable)

    def open_tabix_file(self, filename, index_filename=None):
        return self.repo.open_tabix_file(self, filename, index_filename)


class GenomicResourceRepo(abc.ABC):
    def __init__(self, repo_id):
        self.repo_id: str = repo_id

    @abc.abstractmethod
    def get_resource(self, resource_id, version_constraint=None,
                     genomic_repository_id=None) -> Optional[GenomicResource]:
        '''
            Returns one resource with id qual to resource_id. If not found,
            None is returned.
        '''
        pass

    @abc.abstractmethod
    def get_all_resources(self) -> List[GenomicResource]:
        '''
        Returns a list of GenomicResource objects stored in the repository.
        '''
        pass


class GenomicResourceRealRepo(GenomicResourceRepo):

    def build_genomic_resource(
            self, resource_id, version, config=None,
            manifest: Optional[Manifest]=None):
        
        if not config:
            gr_base = GenomicResource(resource_id, version, self)
            config = gr_base.load_yaml(GR_CONF_FILE_NAME)

        resource = GenomicResource(resource_id, version, self, config)
        resource._manifest = manifest
        return resource

    def get_resource(self, resource_id, version_constraint=None,
                     genomic_repository_id=None) -> Optional[GenomicResource]:

        if genomic_repository_id and self.repo_id != genomic_repository_id:
            return None

        matching_resources = []
        for gr in self.get_all_resources():
            if gr.resource_id != resource_id:
                continue
            if is_version_constraint_satisfied(version_constraint, gr.version):
                matching_resources.append(gr)
        if not matching_resources:
            return None
        return cast(
            GenomicResource,
            max(matching_resources, key=lambda x: x.version))  # type: ignore

    def load_yaml(self, genomic_resource, filename):
        content = self.get_file_content(
            genomic_resource, filename, uncompress=True)
        return yaml.safe_load(content)

    def get_file_content(
            self, genomic_resource, filename, uncompress=True, mode="t"):
        """Returns content of a file in given resource"""
        with self.open_raw_file(
                genomic_resource, filename, mode=f"r{mode}",
                uncompress=uncompress) as infile:
            return infile.read()

    @abc.abstractmethod
    def get_files(self, genomic_resource) -> List[Tuple[str, int, str]]:
        """Returns a list of files for given resource

        For each file in the resource returns a tuple, containing the
        file name, file size and file timestamp.
        """

    @abc.abstractmethod
    def file_exists(self, genomic_resource, filename):
        """Check if given file exist in give resource"""

    @abc.abstractmethod
    def open_raw_file(self, genomic_resource, filename,
                      mode="rt", uncompress=False, seekable=False):
        """Opens file in a resource and returns a file-like object"""

    @abc.abstractmethod
    def open_tabix_file(self, genomic_resource,  filename,
                        index_filename=None):
        """
        Open a tabix file in a resource and return a pysam tabix file object.

        Not all repositories support this method. Repositories that do
        no support this method raise and exception.
        """
