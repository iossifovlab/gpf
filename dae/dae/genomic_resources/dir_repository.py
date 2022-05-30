import pathlib
import yaml
import hashlib
import os
import gzip
import pysam  # type: ignore
import logging
import datetime

from typing import Optional

from .repository import GenomicResource
from .repository import GenomicResourceRepo
from .repository import GenomicResourceRealRepo
from .repository import find_genomic_resources_helper
from .repository import find_genomic_resource_files_helper
from .repository import GRP_CONTENTS_FILE_NAME

logger = logging.getLogger(__name__)


class GenomicResourceDirRepo(GenomicResourceRealRepo):
    def __init__(self, repo_id, directory, **atts):
        super().__init__(repo_id)
        self.directory = pathlib.Path(directory)
        self._all_resources = None

    def _dir_to_dict(self, dr):
        if dr.is_dir():
            return {ch.name: self._dir_to_dict(ch) for ch in dr.iterdir()}
        else:
            return dr

    def get_genomic_resource_dir(self, genomic_resource):
        return self.directory / genomic_resource.get_genomic_resource_dir()

    def get_file_path(self, genomic_resource, file_name):
        return self.directory / genomic_resource.get_genomic_resource_dir() / \
            file_name

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

        def my_leaf_to_size_and_time(ff):
            sts = ff.stat()

            return sts.st_size, \
                datetime.datetime.fromtimestamp(
                    int(sts.st_mtime), datetime.timezone.utc).isoformat()
        yield from find_genomic_resource_files_helper(
            content_dict, my_leaf_to_size_and_time)

    def file_exists(self, genomic_resource, filename):
        full_file_path = self.get_file_path(genomic_resource, filename)
        return os.path.exists(full_file_path)

    def open_raw_file(self, genomic_resource: GenomicResource, filename: str,
                      mode=None, uncompress=False, _seekable=False):
        fullFilePath = self.get_file_path(genomic_resource, filename)
        if 'w' in mode:
            # Create the containing directory if it doesn't exists.
            # This align DireRepo API with URL and fspec APIs
            dirname = os.path.dirname(fullFilePath)
            if dirname:
                os.makedirs(dirname, exist_ok=True)
        if filename.endswith(".gz") and uncompress:
            return gzip.open(fullFilePath, "rb")
        else:
            return open(fullFilePath, mode)

    def update_resource(
            self, src_gr: GenomicResource):

        dest_gr: Optional[GenomicResource] = self.get_resource(
            src_gr.resource_id, f"={src_gr.get_version_str()}")
        assert dest_gr is not None

        assert dest_gr.repo == self
        mnfst_dest = dest_gr.get_manifest()
        mnfst_src = src_gr.get_manifest()

        if mnfst_dest == mnfst_src:
            logger.debug(f"nothing to update {dest_gr.resource_id}")
            return

        manifest_diff = {}
        for dest_file in mnfst_dest:
            manifest_diff[dest_file["name"]] = [dest_file, None]
        for source_file in mnfst_src:
            if source_file["name"] in manifest_diff:
                manifest_diff[source_file["name"]][1] = source_file
            else:
                manifest_diff[source_file["name"]] = [None, source_file]

        result_manifest = []
        for dest_file, src_file in manifest_diff.values():

            if dest_file is None and src_file:
                # copy src_file
                dest_mnfst = self._copy_manifest_entry(
                    dest_gr, src_gr, src_file)
                result_manifest.append(dest_mnfst)
            elif dest_file and src_file is None:
                # delete dest_file
                self._delete_manifest_entry(
                    dest_gr, dest_file)

            elif dest_file != src_file:
                # update src_file
                dest_mnfst = self._copy_manifest_entry(
                    dest_gr, src_gr, src_file)
                result_manifest.append(dest_mnfst)
            else:
                result_manifest.append(dest_file)

        dest_gr.save_manifest(result_manifest)

    def _delete_manifest_entry(
            self, dest_gr: GenomicResource, dest_mnfst_file):
        filename = dest_mnfst_file["name"]

        dr = pathlib.Path(
            self.directory /
            dest_gr.get_genomic_resource_dir() / filename).parent

        dest_path = dr / filename
        dest_path.unlink()

    def _copy_manifest_entry(
            self, dest_gr: GenomicResource, src_gr: GenomicResource,
            src_mnfst_file):

        assert dest_gr.resource_id == src_gr.resource_id
        filename = src_mnfst_file["name"]

        dest_filename = pathlib.Path(
            self.directory /
            dest_gr.get_genomic_resource_dir() / filename)
        os.makedirs(dest_filename.parent, exist_ok=True)

        try:
            with src_gr.open_raw_file(
                    filename, "rb",
                    uncompress=False) as infile, \
                    dest_gr.open_raw_file(
                        filename, 'wb',
                        uncompress=False) as outfile:

                md5_hash = hashlib.md5()
                while b := infile.read(32768):
                    outfile.write(b)
                    md5_hash.update(b)
            md5 = md5_hash.hexdigest()

            if src_mnfst_file["md5"] != md5:
                logger.error(
                    f"storing {src_gr.resource_id} failed; "
                    f"expected md5 is {src_mnfst_file['md5']}; "
                    f"calculated md5 for the stored file is {md5}")
                raise IOError(f"storing of {src_gr.resource_id} failed")
            src_modtime = datetime.datetime.fromisoformat(
                src_mnfst_file["time"]).timestamp()

            assert dest_filename.exists()

            os.utime(dest_filename, (src_modtime, src_modtime))
            return src_mnfst_file
        except Exception:
            logger.error(
                "problem copying remote resource file: %s (%s)", 
                filename, src_gr.resource_id, exc_info=True)
            return None

    def store_all_resources(self, source_repo: GenomicResourceRepo):
        for gr in source_repo.get_all_resources():
            self.store_resource(gr)

    def store_resource(self, resource: GenomicResource):
        manifest = resource.get_manifest()

        temp_gr = GenomicResource(resource.resource_id,
                                  resource.version, self)
        for mnf_file in manifest:
            dest_mnf_file = \
                self._copy_manifest_entry(temp_gr, resource, mnf_file)
            if dest_mnf_file is None:
                logger.error(
                    "unable to copy a (%s) manifest entry: %s",
                    resource.resource_id, mnf_file["name"])
                logger.error(
                    "skipping resource: %s", resource.resource_id)
                self._all_resources = None
                return
                
            assert dest_mnf_file == mnf_file

        # new_gr = self.get_resource(
        #     resource.resource_id,
        #    f"={resource.get_version_str()}")
        temp_gr.save_manifest(manifest)
        self._all_resources = None

    def build_repo_content(self):
        content = [{"id": gr.resource_id, "version": gr.get_version_str(),
                    "config": gr.get_config(), "manifest": gr.get_manifest()}
                   for gr in self.get_all_resources()]
        content = sorted(content, key=lambda x: x['id'])
        return content

    def save_content_file(self):
        content_filename = self.directory / GRP_CONTENTS_FILE_NAME
        logger.debug(f"saving contents file {content_filename}")
        content = self.build_repo_content()
        with open(content_filename, "w") as CF:
            yaml.dump(content, CF)

    def open_tabix_file(self, genomic_resource,  filename,
                        index_filename=None):
        file_path = str(self.get_file_path(genomic_resource, filename))
        index_path = None
        if index_filename:
            index_path = str(self.get_file_path(
                genomic_resource, index_filename))
        return pysam.TabixFile(file_path, index=index_path)
