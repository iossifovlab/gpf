from .repository import GenomicResource
from .repository import GenomicResourceRealRepo
from .repository import find_genomic_resources_helper
from .repository import find_genomic_resource_files_helper
from .repository import GR_ENCODING

import gzip
import io
import time
import datetime


class GenomicResourceEmbededRepo(GenomicResourceRealRepo):
    def __init__(self, repo_id, content, **atts):
        super().__init__(repo_id)
        self.content = content
        self.stable_timestamp = datetime.datetime.fromtimestamp(
            int(time.time())).isoformat()

    def get_all_resources(self):
        for grId, grVr in find_genomic_resources_helper(self.content):
            yield self.build_genomic_resource(grId, grVr)

    def file_exists(self, genomic_resource, filename):
        try:
            self.get_file_content(genomic_resource, filename, uncompress=False)
            return True
        except Exception:
            return False

    def get_file_content(self, genomic_resource: GenomicResource, filename,
                         uncompress=True):
        content = self._get_file_content_and_time(
            genomic_resource, filename)[0]
        if uncompress and filename.endswith(".gz"):
            content = gzip.decompress(content)
        return content

    def _get_content_and_time(self, leaf_data):
        if isinstance(leaf_data, list) and len(leaf_data) == 2:
            content = leaf_data[0]
            tm = leaf_data[1]
        else:
            content = leaf_data
            tm = self.stable_timestamp
        if isinstance(content, str):
            content = bytes(content, GR_ENCODING)
        return content, tm

    def _get_file_content_and_time(self,
                                   genomic_resource: GenomicResource,
                                   filename: str):
        path_array = genomic_resource.get_genomic_resource_dir().split("/") + \
            filename.split("/")
        d = self.content
        for t in path_array[:-1]:
            if t == "":
                continue
            if t not in d or not isinstance(d[t], dict):
                raise ValueError("not a valid file name")
            d = d[t]
        lt = path_array[-1]
        if lt not in d or isinstance(d[lt], dict):
            raise ValueError("not a valid file name")

        return self._get_content_and_time(d[lt])

    def open_raw_file(self, genomic_resource, filename,
                      mode=None, uncompress=False, seekable=False):
        content = self.get_file_content(genomic_resource, filename, uncompress)
        if filename.endswith(".gz") and uncompress:
            raise Exception("Can't handle uncompressing zip files yet!")
        mode = mode if mode else "rb"
        if 'w' in mode:
            raise Exception("Can't handle writable files yet!")
        if 'b' in mode:
            return io.BytesIO(content)
        else:
            return io.StringIO(content.decode(GR_ENCODING))

    def get_files(self, genomic_resource):
        path_array = genomic_resource.get_genomic_resource_dir().split("/")

        content_dict = self.content
        for token in path_array:
            if token == "":
                continue
            content_dict = content_dict[token]

        def my_leaf_to_size_and_time(v):
            content, tm = self._get_content_and_time(v)
            return len(content), tm

        yield from find_genomic_resource_files_helper(
            content_dict, my_leaf_to_size_and_time)

    def open_tabix_file(self, genomic_resource,  filename,
                        index_filename=None):
        raise ValueError(
            "Tabix files are not supported by GenomicResourceEmbededRepo.")
