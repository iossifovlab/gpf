import io
import gzip
from urllib.request import urlopen
import yaml
import logging
import pysam  # type: ignore
import fsspec  # type: ignore

from urllib.parse import urlparse


from .repository import GenomicResource
from .repository import GenomicResourceRealRepo
from .repository import GRP_CONTENTS_FILE_NAME
from .repository import GR_ENCODING


logger = logging.getLogger(__name__)


class GenomicResourceURLRepo(GenomicResourceRealRepo):
    def __init__(self, repo_id, url, **atts):
        super().__init__(repo_id)
        self.url = url
        if self.url.endswith("/"):
            self.url = self.url[:-1]

        self.scheme = urlparse(url).scheme
        self.filesystem, _ = fsspec.core.url_to_fs(self.url)
        self._all_resources = None

    def get_all_resources(self):
        if self._all_resources is None:
            self._all_resources = []
            url = f"{self.url}/{GRP_CONTENTS_FILE_NAME}"
            logger.debug(f"url repo to open: {url}")
            contents = yaml.safe_load(self.filesystem.open(url))

            for rdf in contents:
                version = tuple(map(int, rdf['version'].split(".")))
                resource = self.build_genomic_resource(
                    rdf['id'], version, config=rdf['config'],
                    manifest=rdf['manifest'])
                logger.debug(
                    f"url repo caching resource {resource.resource_id}")
                self._all_resources.append(resource)
        yield from self._all_resources

    def get_files(self, gr: GenomicResource):
        mnfst = gr.get_manifest()
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

        if self.scheme in ["http", "https"] and not seekable:
            binary_stream = urlopen(file_url)
        else:
            binary_stream = self.filesystem.open(file_url)

        if filename.endswith(".gz") and uncompress:
            return gzip.open(binary_stream, mode)

        if 't' in mode:
            return io.TextIOWrapper(binary_stream, encoding=GR_ENCODING)

        return binary_stream

    def open_tabix_file(self, genomic_resource,  filename,
                        index_filename=None):
        if self.scheme not in ['http', 'https', 's3']:
            raise Exception(
                f"Tabix files are not supported by GenomicResourceURLRepo "
                f"for URLs with scheme {self.scheme}. Only http(s) URLs allow "
                f"the direct access needed by tabix")
        file_url = self.get_file_url(genomic_resource, filename)
        index_url = self.get_file_url(genomic_resource, index_filename) \
            if index_filename else None
        return pysam.TabixFile(file_url, index=index_url)
