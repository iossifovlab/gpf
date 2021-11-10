from __future__ import annotations

import re
import logging
import yaml
import abc
import hashlib

logger = logging.getLogger(__name__)


GR_CONF_FILE_NAME = "genomic_resource.yaml"
GR_MANIFEST_FILE_NAME = ".MANIFEST"
GRP_CONTENTS_FILE_NAME = ".CONTENTS"

GR_ENCODING = 'utf-8'

_GR_ID_TOKEN_RE = re.compile('[a-zA-Z0-9._-]+')


def is_gr_id_token(token):
    '''
        Genomic Resource Id Token is a string with one or more letters,
        numbers, '.', '_', or '-'. The function checks if the parameter
        token is a Genomic REsource Id Token.
    '''
    return bool(_GR_ID_TOKEN_RE.fullmatch(token))


_GR_ID_WITH_VERSION_TOKEN_RE = re.compile(
    r'([a-zA-Z0-9._-]+)(?:\[([1-9]\d*(?:\.\d+)*)\])?')


def parse_gr_id_version_token(token):
    '''
        Genomic Resource Id Version Token is a Genomic Resource Id Token with
        an optional version appened. If present, the version suffix has the
        form "[3.3.2]". The default version is [0].
        Returns None if s in not a Genomic Resource Id Version. Otherwise
        returns token,version tupple
    '''
    match = _GR_ID_WITH_VERSION_TOKEN_RE.fullmatch(token)
    if not match:
        return None
    token = match[1]
    versionS = match[2]
    if versionS:
        versionT = tuple(map(int, versionS.split(".")))
    else:
        versionT = (0,)
    return token, versionT


def version_tuple_to_suffix(versionT):
    if versionT == (0,):
        return ""
    return "[" + ".".join(map(str, versionT)) + "]"


VERSION_CONSTRAINT_RE = re.compile(r'(>=|=)?(\d+(?:\.\d+)*)')


def is_version_constraint_satisfied(version_constraint, version):
    if not version_constraint:
        return True
    match = VERSION_CONSTRAINT_RE.fullmatch(version_constraint)
    if not match:
        raise ValueError(f'Wrong version constrainted {version_constraint}')
    op = match[1] if match[1] else '>='
    constraintVersion = tuple(map(int, match[2].split(".")))
    if op == '=':
        return version == constraintVersion
    if op == '>=':
        return version >= constraintVersion
    raise ValueError(
        f'worng operation {op} in version constraint {version_constraint}')


def find_genomic_resource_files_helper(contentDict, leaf_to_size_and_date,
                                       pref=[]):
    for name, content in contentDict.items():
        if name[0] == '.':
            continue
        nxt = pref + [name]
        if isinstance(content, dict):
            yield from find_genomic_resource_files_helper(
                content, leaf_to_size_and_date, nxt)
        else:
            sz, tm = leaf_to_size_and_date(content)
            yield "/".join(nxt), sz, tm


def find_genomic_resources_helper(content_dict, id_pref=[]):
    n_resources = 0
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
            GRIdToken, GRVersion = idvr
            yield "/".join(id_pref + [GRIdToken]), GRVersion
            n_resources += 1
        else:
            currId = id_pref + [name]
            currIdS = "/".join(currId)
            if not isinstance(content, dict):
                logger.warning(f"The file {currIdS} is not used.")
                continue
            if not is_gr_id_token(name):
                logger.warning(
                    f"The directory {currIdS} has a name {name} that is not a "
                    "valid Genomic Resoruce Id Token.")
                continue
            dirNResourceN = 0
            for grId, grVr in find_genomic_resources_helper(content, currId):
                yield grId, grVr
                n_resources += 1
                dirNResourceN += 1
            if dirNResourceN == 0:
                unused_dirs.add(currIdS)
    if n_resources > 0:
        for drId in unused_dirs:
            logger.warning(f"The directory {drId} contains no resources.")


class GenomicResource:
    def __init__(self, resource_id, version, repo: GenomicResourceRealRepo,
                 config=None):
        self.resource_id = resource_id
        self.version = version
        self.config = config
        self.repo = repo

    @staticmethod
    def get_resource_type():
        return "Basic"

    def get_id(self):
        return self.resource_id

    def get_config(self):
        return self.config

    def get_version_str(self) -> str:
        '''returns string of the form 3.1'''
        return ".".join(map(str, self.version))

    def get_genomic_resource_dir(self) -> str:
        '''
        returns a string of the form aa/bb/cc[3.2] for a genomic resource with
        id aa/bb/cc and version 3.2.
        If the version is 0 the string will be aa/bb/cc.
        '''
        return f"{self.resource_id}{version_tuple_to_suffix(self.version)}"

    def get_files(self):
        '''
        Returns a generator returning (filename,filesize,filetime) for each of
        the files in the genomic resource.
        Files and directories staring with "." are ignored.
        '''
        return self.repo.get_files(self)

    def get_md5_sum(self, filename):
        with self.open_raw_file(filename, "rb") as infile:
            md5_hash = hashlib.md5()
            while d := infile.read(8192):
                md5_hash.update(d)
        return md5_hash.hexdigest()

    def build_manifest(self):
        return [{"name": fn, "size": fs, "time": ft,
                 "md5": self.get_md5_sum(fn)}
                for fn, fs, ft in sorted(self.get_files())]

    def update_manifest(self):
        try:
            currentManifest = self.load_manifest()
            currentManifestD = {x['name']: x for x in currentManifest}
            newManifest = []
            for fn, fs, ft in sorted(self.get_files()):
                md5 = None
                if fn in currentManifestD:
                    cmnF = currentManifestD[fn]
                    if cmnF["size"] == fs and cmnF["time"] == ft:
                        md5 = currentManifestD[fn]["md5"]
                    else:
                        print(f"Updating md5 sum for file {fn}"
                              "for resource {self.id}")
                else:
                    print(
                        f"Found a new file {fn} for resource "
                        f"{self.resource_id}")
                if not md5:
                    md5 = self.get_md5_sum(fn)
                newManifest.append(
                    {"name": fn, "size": fs, "time": ft, "md5": md5})
            if newManifest != currentManifest:
                self.save_manifest(newManifest)
        except Exception:
            print(f"Building a new manifest for resource {self.resource_id}")
            manifest = self.build_manifest()
            self.save_manifest(manifest)

    def load_manifest(self):
        return self.load_yaml(GR_MANIFEST_FILE_NAME)

    def save_manifest(self, manifest):
        with self.open_raw_file(GR_MANIFEST_FILE_NAME, "wt") as MOF:
            yaml.dump(manifest, MOF)

    def get_manifest(self):
        try:
            return self.load_manifest()
        except Exception:
            return self.build_manifest()

    def load_yaml(self, filename):
        return self.repo.load_yaml(self, filename)

    def get_file_content(self, filename, uncompress=True):
        return self.repo.get_file_content(self, filename, uncompress)

    def get_file_str_content(self, filename, uncompress=True):
        return self.get_file_content(filename, uncompress).decode(GR_ENCODING)

    def open_raw_file(self, filename, mode=None, uncompress=False):
        return self.repo.open_raw_file(self, filename, mode, uncompress)

    def open_tabix_file(self, filename, index_filename=None):
        return self.repo.open_tabix_file(self, filename, index_filename)

    def update_stats(self):
        pass


_registered_genomic_resource_types = {}


def register_genomic_resource_type(constructor):
    tp = constructor.get_resource_type()
    if tp in _registered_genomic_resource_types:
        raise Exception(f"The resource {tp} is registered twice!")
    _registered_genomic_resource_types[tp] = constructor


class GenomicResourceRepo(abc.ABC):
    def __init__(self):
        pass

    @abc.abstractmethod
    def get_resource(self, resource_id, version_constraint=None,
                     genomic_repository_id=None) -> GenomicResource:
        '''
            Returns one resource with id qual to resource_id. If not found,
            None is returned.
        '''
        pass

    @abc.abstractmethod
    def get_all_resources(self):
        '''
        Returns a list of GenomicResource objects stored in the repository.
        '''
        pass


class GenomicResourceRealRepo(GenomicResourceRepo):
    def __init__(self, repo_id):
        super().__init__()
        self.repo_id = repo_id

    def build_genomic_resource(self, id, version):
        grTemp = GenomicResource(id, version, self)
        resourceConfig = grTemp.load_yaml(GR_CONF_FILE_NAME)
        grClass = GenomicResource
        if isinstance(resourceConfig, dict) and "type" in resourceConfig:
            grClassType = resourceConfig["type"]
            try:
                grClass = _registered_genomic_resource_types[grClassType]
            except KeyError:
                raise Exception(
                    f"Unknown genomic resource type {grClassType}. The known "
                    f"resource types are: " +
                    ", ".join(sorted(
                        _registered_genomic_resource_types.keys())))
        return grClass(id, version, self, resourceConfig)

    def get_resource(self, resource_id, version_constraint=None,
                     genomic_repository_id=None) -> GenomicResource:
        if genomic_repository_id and self.repo_id != genomic_repository_id:
            return None

        matchingGRs = []
        for gr in self.get_all_resources():
            if gr.resource_id != resource_id:
                continue
            if is_version_constraint_satisfied(version_constraint, gr.version):
                matchingGRs.append(gr)
        if not matchingGRs:
            return None
        return max(matchingGRs, key=lambda x: x.version)

    def load_yaml(self, genomic_resource, filename):
        content = self.get_file_content(genomic_resource, filename, True)
        return yaml.safe_load(content)

    def get_file_content(self, genomic_resource, filename, uncompress=True):
        with self.open_raw_file(genomic_resource, filename, "rb",
                                uncompress) as F:
            return F.read()

    @abc.abstractmethod
    def get_files(self, genomicResource):
        raise Exception("Should not be called!")

    @abc.abstractmethod
    def open_raw_file(self, genomic_resource, filename,
                      mode=None, uncompress=False):
        raise Exception("Should not be called!")

    @abc.abstractmethod
    def open_tabix_file(self, genomic_resource,  filename,
                        index_filename=None):
        raise Exception("Should not be called!")
