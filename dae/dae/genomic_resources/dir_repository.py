"""Defines directory genomic resources repository."""

import pathlib
import hashlib
import os
import gzip
import logging

from typing import List, Tuple, cast

import yaml
import pysam  # type: ignore

from .repository import GR_MANIFEST_FILE_NAME, GenomicResource,\
    ManifestEntry, Manifest
from .repository import GenomicResourceRepo
from .repository import GenomicResourceRealRepo
from .repository import find_genomic_resources_helper
from .repository import find_genomic_resource_files_helper
from .repository import GRP_CONTENTS_FILE_NAME

logger = logging.getLogger(__name__)


class GenomicResourceDirRepo(GenomicResourceRealRepo):
    """Provides directory genomic resources repository."""

    def __init__(  # pylint: disable=unused-argument
        self, repo_id, directory, **kwargs
    ):
        super().__init__(repo_id)
        self.directory: pathlib.Path = pathlib.Path(directory)
        self.directory.mkdir(exist_ok=True, parents=True)
        self._all_resources = None

    def _dir_to_dict(self, directory):
        if not directory.exists():
            return {}
        if directory.is_dir():
            result = {}
            for entry in directory.iterdir():
                if entry.name in {".", ".."}:
                    continue
                if entry.name.startswith("."):
                    continue
                result[entry.name] = self._dir_to_dict(entry)
            return result

        return directory

    def refresh(self):
        """Clears the content of the whole repository and trigers rescan."""
        self._all_resources = None

    def _get_resource_dir(self, resource) -> pathlib.Path:
        """Returns directory for specified resources."""
        return cast(
            pathlib.Path,
            self.directory / resource.get_genomic_resource_id_version())

    def get_all_resources(self):
        """Returns generator for all resources in the repository."""
        if self._all_resources is None:
            dir_content = self._dir_to_dict(self.directory)
            self._all_resources = [self.build_genomic_resource(gr_id, gr_vr)
                                   for gr_id, gr_vr in
                                   find_genomic_resources_helper(dir_content)]
        yield from self._all_resources

    def get_files(self, resource) -> List[Tuple[str, int, str]]:
        """Returns a list of tuples for all files in a resources."""
        content_dict = self._dir_to_dict(
            self._get_resource_dir(resource))

        def my_leaf_to_size_and_time(filepath):
            filestat = filepath.stat()
            filetime = ManifestEntry.convert_timestamp(filestat.st_mtime)
            return filestat.st_size, filetime

        return list(find_genomic_resource_files_helper(
            content_dict, my_leaf_to_size_and_time))

    def get_filepath(self, resource, filename: str) -> pathlib.Path:
        """Returns pathlib filename for a file in a resource."""
        return self._get_resource_dir(resource) / filename

    def get_content_filepath(self):
        """Returns pathlib filename the repository content file."""
        return self.directory / GRP_CONTENTS_FILE_NAME

    def file_exists(self, resource, filename):
        """Checks if a file exists in a genomic resource."""
        full_file_path = self.get_filepath(resource, filename)
        return full_file_path.exists()

    def file_local(self, genomic_resource, filename):
        """Check if a given file in a given resource can be accessed locally"""
        return True

    def open_raw_file(self, resource: GenomicResource, filename: str,
                      mode="rt", uncompress=False, _seekable=False):

        filepath = self.get_filepath(resource, filename)
        if "w" in mode:
            # Create the containing directory if it doesn't exists.
            # This align DireRepo API with URL and fspec APIs
            dirname = os.path.dirname(filepath)
            if dirname:
                os.makedirs(dirname, exist_ok=True)
        if filename.endswith(".gz") and uncompress:
            if "w" in mode:
                raise IOError("writing gzip files not supported")
            return gzip.open(filepath, mode)

        return open(filepath, mode)  # pylint: disable=unspecified-encoding

    def _delete_manifest_entry(
            self, resource: GenomicResource, manifest_entry):
        filename = manifest_entry.name

        filepath = self.get_filepath(resource, filename)
        filepath.unlink(missing_ok=True)

    def _copy_manifest_entry(
            self, dest_resource: GenomicResource,
            src_resource: GenomicResource,
            manifest_entry: ManifestEntry):

        assert dest_resource.resource_id == src_resource.resource_id
        assert dest_resource.repo == self

        filename = manifest_entry.name

        dest_filepath = self.get_filepath(dest_resource, filename)
        dest_filepath.parent.mkdir(parents=True, exist_ok=True)

        if dest_filepath.exists():
            dest_stat = dest_filepath.stat()
            dest_time = ManifestEntry.convert_timestamp(dest_stat.st_mtime)
            dest_size = dest_stat.st_size
            if dest_size == manifest_entry.size and \
                    dest_time == manifest_entry.time:

                logger.debug(
                    "resource <%s> file <%s> already cached and up-to-date",
                    src_resource.resource_id, filename)
                return manifest_entry

            logger.warning(
                "resource %s file %s already cached "
                "but (size, timestamp) does not match: %s,%s != %s,%s",
                src_resource.resource_id, filename,
                dest_size, dest_time,
                manifest_entry.size, manifest_entry.time)

        logger.debug(
            "copying resource (%s) file: %s",
            src_resource.resource_id, filename)
        with src_resource.open_raw_file(
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

        if manifest_entry.md5 != md5:
            logger.error(
                "storing %s failed; expected md5 is %s; "
                "calculated md5 for the stored file is %s",
                src_resource.resource_id, manifest_entry.md5, md5)
            raise IOError(f"storing of {src_resource.resource_id} failed")

        src_modtime = manifest_entry.get_timestamp()
        assert dest_filepath.exists()

        os.utime(dest_filepath, (src_modtime, src_modtime))
        return manifest_entry

    def store_all_resources(self, source_repo: GenomicResourceRepo):
        """Copies all resources from another genomic resources repository."""
        for resource in source_repo.get_all_resources():
            self.store_resource(resource)

    def store_resource(self, remote_resource: GenomicResource):
        """Copies a resources and all it's files."""
        remote_manifest = remote_resource.get_manifest()

        local_resource = self.get_resource(
            remote_resource.resource_id,
            f"={remote_resource.get_version_str()}")
        if local_resource is None:
            local_resource = GenomicResource(
                remote_resource.resource_id,
                remote_resource.version,
                self)

        for remote_manifest_entry in remote_manifest:
            local_manifest_entry = \
                self._copy_manifest_entry(
                    local_resource, remote_resource, remote_manifest_entry)
            if local_manifest_entry is None:
                logger.error(
                    "unable to copy a (%s) manifest entry: %s",
                    remote_resource.resource_id, remote_manifest_entry.name)
                logger.error(
                    "skipping resource: %s", remote_resource.resource_id)
                raise IOError(
                    f"unable to copy a ({remote_resource.resource_id}) "
                    f"manifest entry: {remote_manifest_entry.name}")

            assert local_manifest_entry == remote_manifest_entry

        self.save_manifest(local_resource, remote_manifest)
        self.refresh()

    def open_tabix_file(self, resource,  filename,
                        index_filename=None):
        file_path = str(self.get_filepath(resource, filename))
        index_path = None
        if index_filename:
            index_path = str(self.get_filepath(
                resource, index_filename))
        return pysam.TabixFile(  # pylint: disable=no-member
            file_path, index=index_path
        )

    def compute_md5_sum(self, resource, filename):
        """Computes a md5 hash for a file in the resource"""
        logger.debug(
            "compute md5sum for %s in %s", filename, resource.resource_id)
        filepath = self.get_filepath(resource, filename)
        with open(filepath, "rb") as infile:
            md5_hash = hashlib.md5()
            while chunk := infile.read(8192):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()

    def build_manifest(self, resource):
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

    def update_manifest(self, resource):
        """Updates resource manifest and stores it."""
        try:
            current_manifest = self.load_manifest(resource)
            new_manifest = Manifest()
            for fname, fsize, ftime in sorted(self.get_files(resource)):
                md5 = None
                if fname in current_manifest:
                    entry = current_manifest[fname]
                    if entry.size == fsize and entry.time == ftime:
                        md5 = entry.md5
                    else:
                        logger.debug(
                            "md5 sum for file %s for resource %s needs update",
                            fname, resource.resource_id)
                else:
                    logger.debug(
                        "found a new file %s for resource %s",
                        fname, resource.resource_id)
                if md5 is None:
                    md5 = self.compute_md5_sum(resource, fname)
                new_manifest.add(
                    ManifestEntry(fname, fsize, ftime, md5))

            if new_manifest == current_manifest:
                logger.debug("manifest OK for %s", resource.resource_id)
            else:
                logger.debug("manifest updated for %s", resource.resource_id)
                self.save_manifest(resource, new_manifest)
        except IOError:
            logger.info(
                "building a new manifest for resource %s",
                resource.resource_id, exc_info=True)
            manifest = self.build_manifest(resource)
            self.save_manifest(resource, manifest)

    def load_manifest(self, resource) -> Manifest:
        """Loads resource manifest"""
        filename = self.get_filepath(resource, GR_MANIFEST_FILE_NAME)
        with open(filename, "rt", encoding="utf8") as infile:
            content = infile.read()
            return Manifest.from_file_content(content)

    def save_manifest(self, resource, manifest: Manifest):
        """Saves manifest into genomic resources directory."""
        filename = self.get_filepath(resource, GR_MANIFEST_FILE_NAME)
        with open(filename, "wt", encoding="utf8") as outfile:
            yaml.dump(manifest.to_manifest_entries(), outfile)
        resource.refresh()

    def get_manifest(self, resource):
        """Loads or build a resource manifest."""
        try:
            manifest = self.load_manifest(resource)
            return manifest
        except FileNotFoundError:
            manifest = self.build_manifest(resource)
            return manifest
