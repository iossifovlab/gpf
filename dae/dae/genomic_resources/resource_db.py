import os
from urllib.parse import urlparse
from dae.genomic_resources.repository import FSGenomicResourcesRepo, \
    HTTPGenomicResourcesRepo
from dae.genomic_resources.resources import GenomicResourceBase


class GenomicResourceDB:
    def __init__(self, resources_config):
        self.config = resources_config
        self._cache = FSGenomicResourcesRepo(
            "cache", self.config.cache_location
        )
        self.repositories = []
        for gsd_conf in self.config.genomic_resource_repositories:
            gsd_id = gsd_conf["id"]
            gsd_url = urlparse(gsd_conf["url"])
            is_filesystem = gsd_url.scheme == "file"
            if is_filesystem:
                gsd = FSGenomicResourcesRepo(gsd_id, gsd_url.path)
            else:
                gsd = HTTPGenomicResourcesRepo(gsd_id, gsd_url.geturl())
            self.repositories.append(gsd)

    def get_resource(self, resource_id: str):
        resource = self.cache.get_resource(resource_id)
        if resource is not None:
            return resource

        for repository in self.repositories:
            resource = repository.get_resource(resource_id)
            if resource is not None:
                self._do_cache(resource)
                return self.get_resource(resource_id)

        return None

    def get_cache(self):
        return self._cache

    def _do_cache(self, resource: GenomicResourceBase):
        cache_path = os.path.join(
            self._cache.get_url(), resource.get_url()
        )
        os.makedirs(cache_path, exist_ok=True)

        def copy_file(filename: str):
            output_path = os.path.join(cache_path, filename)
            with open(output_path, "wb") as destination_file:
                for chunk in resource.get_repo().stream_resource_file(
                        resource.get_id(), filename):
                    destination_file.write(chunk)

        for file in resource.get_manifest().keys():
            copy_file(file)

        self._cache_gsd.reload()

    def cache_resource(self, resource_id: str):
        for repository in self.repositories:
            resource = repository.get_resource(resource_id)
            if resource is not None:
                self._do_cache(resource)
                return
