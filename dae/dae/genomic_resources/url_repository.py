import io
import gzip
import yaml
import pysam
from urllib.request import urlopen
from urllib.parse import urlparse


from .repository import GenomicResource
from .repository import GenomicResourceRealRepo
from .repository import GRP_CONTENTS_FILE_NAME
from .repository import GR_ENCODING
from .http_file import HTTPFile


class GenomicResourceURLRepo(GenomicResourceRealRepo):
    def __init__(self, repo_id, url, **atts):
        super().__init__(repo_id)
        self.url = url
        self.scheme = urlparse(url).scheme

    def get_all_resources(self):
        contents = yaml.safe_load(
            urlopen(self.url + "/" + GRP_CONTENTS_FILE_NAME))
        for rdf in contents:
            versionT = tuple(map(int, rdf['version'].split(".")))
            yield self.build_genomic_resource(rdf['id'], versionT)

    def get_files(self, genomicResource: GenomicResource):
        mnfst = genomicResource.load_manifest()
        for mnfst in mnfst:
            yield mnfst['name'], int(mnfst['size']), float(mnfst['time'])

    def get_file_url(self, genomic_resource, filename):
        return self.url + "/" + genomic_resource.get_genomic_resource_dir() + \
            "/" + filename

    def open_raw_file(self, genomic_resource: GenomicResource,
                      filename, mode=None,
                      uncompress=False):
        mode = mode if mode else "rb"
        if 'w' in mode:
            raise Exception("Can't handle writable files yet!")

        file_url = self.get_file_url(genomic_resource, filename)
        binarySt = urlopen(file_url)

        if filename.endswith(".gz") and uncompress:
            return gzip.open(binarySt, mode)

        if 't' in mode:
            return io.TextIOWrapper(binarySt, encoding=GR_ENCODING)

        if self.scheme == 'http':
            return HTTPFile(file_url)

        return binarySt

    def open_tabix_file(self, genomic_resource,  filename,
                        index_filename=None):
        if self.scheme != 'http':
            raise Exception(
                f"Tabix files are not supported by GenomicResourceURLRepo "
                f"for URLs with scheme {self.scheme}. Only http URLs allow "
                f"the direct access needed by tabix")
        file_url = self.get_file_url(genomic_resource, filename)
        index_url = self.get_file_url(genomic_resource, index_filename) \
            if index_filename else None
        return pysam.TabixFile(file_url, index=index_url)
