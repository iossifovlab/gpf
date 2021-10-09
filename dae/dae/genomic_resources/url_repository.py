import io
import gzip
import yaml
from urllib.request import urlopen

from .repository import GenomicResource
from .repository import GenomicResourceRealRepo
from .repository import GRP_CONTENTS_FILE_NAME
from .repository import GR_ENCODING


class GenomicResourceURLRepo(GenomicResourceRealRepo):
    def __init__(self, repo_id, url, **atts):
        self.url = url
        super().__init__(repo_id)

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

    def open_raw_file(self, genomic_resource: GenomicResource,
                      filename, mode=None,
                      uncompress=False):
        mode = mode if mode else "rb"
        if 'w' in mode:
            raise Exception("Can't handle writable files yet!")

        binarySt = urlopen(
            self.url + "/" + genomic_resource.get_genomic_resource_dir() +
            "/" + filename)

        if filename.endswith(".gz") and uncompress:
            return gzip.open(binarySt, mode)

        if 't' in mode:
            return io.TextIOWrapper(binarySt, encoding=GR_ENCODING)
        else:
            return binarySt

    def open_tabix_file(self, genomic_resource,  filename,
                        index_filename=None):
        raise Exception(
            "Tabix files are not supported by GenomicResourceURLRepo.")
