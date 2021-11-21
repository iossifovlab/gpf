import io
import gzip
import yaml
import pysam
import logging

from urllib.request import urlopen
from urllib.parse import urlparse


from .repository import GenomicResource
from .repository import GenomicResourceRealRepo
from .repository import GRP_CONTENTS_FILE_NAME
from .repository import GR_ENCODING
from .http_file import HTTPFile


logger = logging.getLogger(__name__)


class GenomicResourceURLRepo(GenomicResourceRealRepo):
    def __init__(self, repo_id, url, **atts):
        super().__init__(repo_id)
        self.url = url
        self.scheme = urlparse(url).scheme
        self._all_resources = None

    def get_all_resources(self):
        if self._all_resources is None:
            self._all_resources = []
            contents = yaml.safe_load(
                urlopen(self.url + "/" + GRP_CONTENTS_FILE_NAME))
            for rdf in contents:
                versionT = tuple(map(int, rdf['version'].split(".")))
                resource = self.build_genomic_resource(
                    rdf['id'], versionT, config=rdf['config'],
                    manifest=rdf['manifest'])
                self._all_resources.append(resource)
        yield from self._all_resources

    def get_files(self, genomicResource: GenomicResource):
        mnfst = genomicResource.get_manifest()
        for mnfst in mnfst:
            yield mnfst['name'], int(mnfst['size']), mnfst['time']

    def get_file_url(self, genomic_resource, filename):
        return self.url + "/" + genomic_resource.get_genomic_resource_dir() + \
            "/" + filename

    def open_raw_file(self, genomic_resource: GenomicResource,
                      filename, mode=None,
                      uncompress=False,
                      seekable=False):

        mode = mode if mode else "rb"
        if 'w' in mode:
            raise Exception("Can't handle writable files yet!")

        file_url = self.get_file_url(genomic_resource, filename)
        logger.debug(f"opening url resource: {file_url}")

        if self.scheme in ['http', 'https'] and seekable:
            logger.debug("using HTTPFile for http(s)")
            binary_stream = HTTPFile(file_url)
            if "t" in mode:
                return io.TextIOWrapper(
                    binary_stream, encoding=GR_ENCODING)
            # if filename.endswith(".gz") and uncompress:
            #     return gzip.open(binary_stream, mode)
            return binary_stream
        else:
            binary_stream = urlopen(file_url)
            if filename.endswith(".gz") and uncompress:
                return gzip.open(binary_stream, mode)

            if 't' in mode:
                return io.TextIOWrapper(binary_stream, encoding=GR_ENCODING)

            return binary_stream

    def open_tabix_file(self, genomic_resource,  filename,
                        index_filename=None):
        if self.scheme not in ['http', 'https']:
            raise Exception(
                f"Tabix files are not supported by GenomicResourceURLRepo "
                f"for URLs with scheme {self.scheme}. Only http(s) URLs allow "
                f"the direct access needed by tabix")
        file_url = self.get_file_url(genomic_resource, filename)
        index_url = self.get_file_url(genomic_resource, index_filename) \
            if index_filename else None
        return pysam.TabixFile(file_url, index=index_url)
