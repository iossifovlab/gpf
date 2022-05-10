"""Defines directory genomic resources repository."""

import pathlib
import hashlib
import os
import gzip
import logging
import datetime

import yaml
import pysam  # type: ignore

from .repository import GenomicResource, ManifestEntry
from .repository import GenomicResourceRepo
from .repository import GenomicResourceRealRepo
from .repository import find_genomic_resources_helper
from .repository import find_genomic_resource_files_helper
from .repository import GRP_CONTENTS_FILE_NAME

logger = logging.getLogger(__name__)


class GenomicResourceDirRepo(GenomicResourceRealRepo):
    """Provides directory genomic resources repository."""

    def __init__(self, repo_id, directory, **kwargs):  # pylint: disable=unused-argument
        super().__init__(repo_id)
        self.directory = pathlib.Path(directory)
        self.directory.mkdir(exist_ok=True, parents=True)
        self._all_resources = None

    def _dir_to_dict(self, directory):
        if directory.is_dir():
            return {
                entry.name: self._dir_to_dict(entry)
                for entry in directory.iterdir()
            }

        return directory

    def refresh(self):
        """Clears the content of the whole repository and trigers rescan."""
        self._all_resources = None

    def get_genomic_resource_dir(self, resource):
        """Returns directory for specified resources."""
        return self.directory / resource.get_genomic_resource_dir()

    def get_file_path(self, resource, file_name):
        """Returns full filename for a file in a resource."""
        return self.get_genomic_resource_dir(resource) / file_name

    def get_all_resources(self):
        """Returns generator for all resources in the repository."""
        if self._all_resources is None:
            dir_content = self._dir_to_dict(self.directory)
            self._all_resources = [self.build_genomic_resource(gr_id, gr_vr)
                                   for gr_id, gr_vr in
                                   find_genomic_resources_helper(dir_content)]
        yield from self._all_resources

    def get_files(self, genomic_resource):
        """Returns a generator for all files in a resources."""
        content_dict = self._dir_to_dict(
            self.get_genomic_resource_dir(genomic_resource))

        def my_leaf_to_size_and_time(filepath):
            filestat = filepath.stat()
            filetimestamp = \
                datetime.datetime.fromtimestamp(int(filestat.st_mtime)).isoformat()
            return filestat.st_size, filetimestamp

        yield from find_genomic_resource_files_helper(
            content_dict, my_leaf_to_size_and_time)

    def file_exists(self, genomic_resource, filename):
        """Checks if a file exists in a genomic resource."""
        full_file_path = self.get_file_path(genomic_resource, filename)
        return os.path.exists(full_file_path)

    def open_raw_file(self, genomic_resource: GenomicResource, filename: str,
                      mode="rt", uncompress=False, _seekable=False):

        full_file_path = self.get_file_path(genomic_resource, filename)
        if 'w' in mode:
            # Create the containing directory if it doesn't exists.
            # This align DireRepo API with URL and fspec APIs
            dirname = os.path.dirname(full_file_path)
            if dirname:
                os.makedirs(dirname, exist_ok=True)
        if filename.endswith(".gz") and uncompress:
            if "w" in mode:
                raise IOError("writing gzip files not supported")
            return gzip.open(full_file_path, mode)

        return open(full_file_path, mode)  # pylint: disable=unspecified-encoding

    def _delete_manifest_entry(
            self, resource: GenomicResource, manifest_entry):
        filename = manifest_entry.name

        filepath = pathlib.Path(
            self.directory /
            resource.get_genomic_resource_dir()) / filename
        filepath.unlink(missing_ok=True)

    def _copy_manifest_entry(
            self, dest_resource: GenomicResource,
            src_resource: GenomicResource,
            manifest_entry: ManifestEntry):

        assert dest_resource.resource_id == src_resource.resource_id
        filename = manifest_entry.name

        dest_filename = pathlib.Path(
            self.directory /
            dest_resource.get_genomic_resource_dir() / filename)
        os.makedirs(dest_filename.parent, exist_ok=True)

        with src_resource.open_raw_file(
                filename, "rb",
                uncompress=False) as infile, \
                dest_resource.open_raw_file(
                    filename, 'wb',
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
        src_modtime = datetime.datetime.fromisoformat(
            manifest_entry.time).timestamp()

        assert dest_filename.exists()

        os.utime(dest_filename, (src_modtime, src_modtime))
        return manifest_entry

    def store_all_resources(self, source_repo: GenomicResourceRepo):
        """Copies all resources from another genomic resources repository."""
        for resource in source_repo.get_all_resources():
            self.store_resource(resource)

    def store_resource(self, resource: GenomicResource):
        """Copies a resources and all it's files."""
        manifest = resource.get_manifest()

        temp_gr = GenomicResource(resource.resource_id,
                                  resource.version, self)
        for manifest_entry in manifest:
            dest_manifest_entry = \
                self._copy_manifest_entry(temp_gr, resource, manifest_entry)
            if dest_manifest_entry is None:
                logger.error(
                    "unable to copy a (%s) manifest entry: %s",
                    resource.resource_id, manifest_entry.name)
                logger.error(
                    "skipping resource: %s", resource.resource_id)
                self.refresh()
                return

            assert dest_manifest_entry == manifest_entry

        temp_gr.save_manifest(manifest)
        self.refresh()

    def build_repo_content(self):
        """Builds the content of the .CONTENTS file."""
        content = [
            {
                "id": gr.resource_id,
                "version": gr.get_version_str(),
                "config": gr.get_config(),
                "manifest": gr.get_manifest().to_manifest_entries()
            }
            for gr in self.get_all_resources()]
        content = sorted(content, key=lambda x: x['id'])
        return content

    def save_content_file(self):
        """Creates and saves the content file for the repository."""
        content_filename = self.directory / GRP_CONTENTS_FILE_NAME
        logger.debug("saving contents file %s", content_filename)
        content = self.build_repo_content()
        with open(content_filename, "wt", encoding="utf8") as outfile:
            yaml.dump(content, outfile)

    def open_tabix_file(self, genomic_resource,  filename,
                        index_filename=None):
        file_path = str(self.get_file_path(genomic_resource, filename))
        index_path = None
        if index_filename:
            index_path = str(self.get_file_path(
                genomic_resource, index_filename))
        return pysam.TabixFile(file_path, index=index_path)  # pylint: disable=no-member
