"""Defines directory genomic resources repository."""

import pathlib
import hashlib
import os
import gzip
import logging
import datetime
from dataclasses import asdict
from typing import Optional

import yaml
import pysam  # type: ignore

from .repository import GenomicResource, ManifestEntry, Manifest
from .repository import GenomicResourceRepo
from .repository import GenomicResourceRealRepo
from .repository import find_genomic_resources_helper
from .repository import find_genomic_resource_files_helper
from .repository import GRP_CONTENTS_FILE_NAME

logger = logging.getLogger(__name__)


class GenomicResourceDirRepo(GenomicResourceRealRepo):
    """Provides directory genomic resources repository."""

    def __init__(self, repo_id, directory, **atts):
        super().__init__(repo_id)
        self.directory = pathlib.Path(directory)
        self._all_resources = None

    def _dir_to_dict(self, directory):
        if directory.is_dir():
            return {
                entry.name: self._dir_to_dict(entry)
                for entry in directory.iterdir()
            }

        return directory

    def get_genomic_resource_dir(self, resource):
        return self.directory / resource.get_genomic_resource_dir()

    def get_file_path(self, resource, file_name):
        return self.get_genomic_resource_dir(resource) / file_name

    def get_all_resources(self):
        if self._all_resources is None:
            d = self._dir_to_dict(self.directory)
            self._all_resources = [self.build_genomic_resource(grId, grVr)
                                   for grId, grVr in
                                   find_genomic_resources_helper(d)]
        yield from self._all_resources

    def get_files(self, genomic_resource):
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
                raise IOError(f"writing gzip files not supported")
            return gzip.open(full_file_path, mode)

        return open(full_file_path, mode)

    def update_resource(
            self, src_gr: GenomicResource):

        dest_gr: Optional[GenomicResource] = self.get_resource(
            src_gr.resource_id, f"={src_gr.get_version_str()}")
        assert dest_gr is not None

        assert dest_gr.repo == self
        mnfst_dest = dest_gr.get_manifest()
        mnfst_src = src_gr.get_manifest()

        if mnfst_dest == mnfst_src:
            logger.debug("nothing to update %s", dest_gr.resource_id)
            return

        manifest_diff = {}
        for dest_file in mnfst_dest:
            manifest_diff[dest_file.name] = [dest_file, None]
        for source_file in mnfst_src:
            if source_file.name in manifest_diff:
                manifest_diff[source_file.name][1] = source_file
            else:
                manifest_diff[source_file.name] = [None, source_file]

        result_manifest = Manifest()
        for dest_file, src_file in manifest_diff.values():

            if (dest_file is None and src_file) or \
                    (dest_file != src_file and src_file is not None):
                # copy src_file or
                # update src_file
                dest_mnfst = self._copy_manifest_entry(
                    dest_gr, src_gr, src_file)
                result_manifest.add(dest_mnfst)
            elif dest_file and src_file is None:
                # delete dest_file
                self._delete_manifest_entry(
                    dest_gr, dest_file)
            else:
                result_manifest.add(dest_file)

        dest_gr.save_manifest(result_manifest)

    def _delete_manifest_entry(
            self, resource: GenomicResource, manifest_entry):
        filename = manifest_entry.name

        filepath = pathlib.Path(
            self.directory /
            resource.get_genomic_resource_dir()) / filename
        filepath.unlink()

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

        try:
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
        except Exception:
            logger.error(
                "problem copying remote resource file: %s (%s)",
                filename, src_resource.resource_id, exc_info=True)
            return None

    def store_all_resources_full(self, source_repo: GenomicResourceRepo):
        for resource in source_repo.get_all_resources():
            self.store_resource_full(resource)

    def store_resource_full(self, resource: GenomicResource):
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
                self._all_resources = None
                return

            assert dest_manifest_entry == manifest_entry

        temp_gr.save_manifest(manifest)
        self._all_resources = None

    def build_repo_content(self):
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
        content_filename = self.directory / GRP_CONTENTS_FILE_NAME
        logger.debug("saving contents file %s", content_filename)
        content = self.build_repo_content()
        with open(content_filename, "w") as outfile:
            yaml.dump(content, outfile)

    def open_tabix_file(self, genomic_resource,  filename,
                        index_filename=None):
        file_path = str(self.get_file_path(genomic_resource, filename))
        index_path = None
        if index_filename:
            index_path = str(self.get_file_path(
                genomic_resource, index_filename))
        return pysam.TabixFile(file_path, index=index_path)  # pylint: disable=no-member
