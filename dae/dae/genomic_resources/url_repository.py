"""Provides URL genomic resources repository"""

import io
import gzip
import logging

from urllib.request import urlopen
from urllib.parse import urlparse

import yaml
import pysam  # type: ignore
import fsspec  # type: ignore

from .repository import GenomicResource, Manifest
from .repository import GenomicResourceRealRepo
from .repository import GR_CONTENTS_FILE_NAME
from .repository import GR_ENCODING


logger = logging.getLogger(__name__)


class GenomicResourceURLRepo(GenomicResourceRealRepo):
    """Defines URL genomic resources repository."""

    def __init__(self, repo_id, url, **_kwargs):
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
            url = f"{self.url}/{GR_CONTENTS_FILE_NAME}"
            logger.debug("url repo to open: %s", url)
            contents = yaml.safe_load(self.filesystem.open(url))

            for rdf in contents:
                version = tuple(map(int, rdf["version"].split(".")))
                manifest = Manifest.from_manifest_entries(rdf["manifest"])
                resource = self.build_genomic_resource(
                    rdf["id"], version, config=rdf["config"],
                    manifest=manifest)
                logger.debug(
                    "url repo caching resource %s", resource.resource_id)
                self._all_resources.append(resource)
        yield from self._all_resources

    # def get_files(self, resource: GenomicResource):
    #     for entry in resource.get_manifest():
    #         yield entry.name, entry.size, entry.time

    def file_exists(self, resource, filename):
        file_url = self._get_file_url(resource, filename)
        return self.filesystem.exists(file_url)

    def _get_file_url(self, resource, filename):
        return self.url + "/" + \
            resource.get_genomic_resource_id_version() + \
            "/" + filename

    def open_raw_file(
            self, resource: GenomicResource, filename,
            mode=None, uncompress=False, seekable=False):

        mode = mode if mode else "rt"

        file_url = self._get_file_url(resource, filename)
        logger.debug("opening url raw file: %s", file_url)

        if self.scheme in ["http", "https"] and not seekable:
            binary_stream = urlopen(file_url)
        else:
            bin_mode = mode.replace("t", "b")
            binary_stream = self.filesystem.open(file_url, bin_mode)

        if filename.endswith(".gz") and uncompress:
            return gzip.open(binary_stream, mode)

        if "b" in mode:
            return binary_stream
        return io.TextIOWrapper(binary_stream, encoding=GR_ENCODING)

    def open_tabix_file(self, resource,  filename,
                        index_filename=None):
        if self.scheme not in ["http", "https", "s3"]:
            raise ValueError(
                f"Tabix files are not supported by GenomicResourceURLRepo "
                f"for URLs with scheme {self.scheme}. Only http(s) URLs allow "
                f"the direct access needed by tabix")
        file_url = self._get_file_url(resource, filename)
        index_url = self._get_file_url(resource, index_filename) \
            if index_filename else None
        return pysam.TabixFile(file_url, index=index_url)  # pylint: disable=no-member
