from .repository import GenomicResource
from .repository import GenomicResourceRepo
from .repository import GenomicResourceRealRepo
from .repository import find_genomic_resources_helper
from .repository import find_genomic_resource_files_helper
from .repository import GRP_CONTENTS_FILE_NAME


import pathlib
import yaml
import hashlib
import os
import gzip
import pysam


class GenomicResourceDirRepo(GenomicResourceRealRepo):
    def __init__(self, repo_id, directory, **atts):
        super().__init__(repo_id)
        self.directory = pathlib.Path(directory)

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
        d = self._dir_to_dict(self.directory)
        for grId, grVr in find_genomic_resources_helper(d):
            yield self.build_genomic_resource(grId, grVr)

    def get_files(self, genomic_resource):
        contentDict = self._dir_to_dict(
            self.get_genomic_resource_dir(genomic_resource))

        def my_leaf_to_size_and_time(ff):
            sts = ff.stat()
            return sts.st_size, sts.st_mtime
        yield from find_genomic_resource_files_helper(
            contentDict, my_leaf_to_size_and_time)

    def open_raw_file(self, genomic_resource: GenomicResource, filename: str,
                      mode=None, uncompress=False):
        fullFilePath = self.get_file_path(genomic_resource, filename)
        if filename.endswith(".gz") and uncompress:
            return gzip.open(fullFilePath, "rb")
        else:
            return open(fullFilePath, mode)

    def update_resource(self, my_gr, other_gr):
        assert my_gr.repo == self
        raise Exception("not yet")

    def store_all_resources(self, source_repo: GenomicResourceRepo):
        for gr in source_repo.get_all_resources():
            self.store_resource(gr)

    def store_resource(self, genomic_resource: GenomicResource):
        manifest = genomic_resource.get_manifest()
        temp_gr = GenomicResource(genomic_resource.resource_id,
                                  genomic_resource.version, self)
        for mnfF in manifest:
            dr = pathlib.Path(self.directory /
                              genomic_resource.get_genomic_resource_dir() /
                              mnfF['name']).parent
            os.makedirs(dr, exist_ok=True)
            with genomic_resource.open_raw_file(mnfF["name"], "rb",
                                                uncompress=False) as IF, \
                    temp_gr.open_raw_file(mnfF["name"], 'wb',
                                          uncompress=False) as OF:
                md5_hash = hashlib.md5()
                while b := IF.read(8192):
                    OF.write(b)
                    md5_hash.update(b)
            if md5_hash.hexdigest() != mnfF["md5"]:
                raise Exception("The copy failed! ")
        new_gr = self.get_resource(
            genomic_resource.resource_id,
            f"={genomic_resource.get_version_str()}")
        new_gr.save_manifest(manifest)

    def save_content_file(self):
        content_filename = self.directory / GRP_CONTENTS_FILE_NAME
        print("Saving contents file", content_filename)
        content = [{"id": gr.resource_id, "version": gr.get_version_str()}
                   for gr in self.get_all_resources()]
        content = sorted(content, key=lambda x: x['id'])
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
