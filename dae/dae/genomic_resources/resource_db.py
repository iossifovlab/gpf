import os
from urllib.parse import urlparse
from dae.genomic_resources.repository import FSGenomicResourcesRepo, \
    HTTPGenomicResourcesRepo, GenomicResourcesRepo
from dae.genomic_resources.resources import GenomicResource


class GenomicResourceDB:
    def __init__(self, repositories):
        self.repositories = []
        for gsd_conf in repositories:
            gsd_id = gsd_conf["id"]
            gsd_url = urlparse(gsd_conf["url"])

            is_filesystem = gsd_url.scheme == "file"
            if is_filesystem:
                gsd = FSGenomicResourcesRepo(gsd_id, gsd_url.path)
            else:
                gsd = HTTPGenomicResourcesRepo(gsd_id, gsd_url.geturl())
            self.repositories.append(gsd)

    def get_resource(self, resource_id: str, repo_id: str = None):
        if repo_id is not None:
            raise NotImplementedError

        for repository in self.repositories:
            resource = repository.get_resource(resource_id)
            if resource is not None:
                return resource

        return None


class CachedGenomicResourceDB(GenomicResourceDB):
    def __init__(self, repositories, cache_location):
        self._cache = FSGenomicResourcesRepo(
            "cache", cache_location
        )
        super(CachedGenomicResourceDB, self).__init__(repositories)

    def get_cache_repo(self):
        return self._cache

    def _do_cache(self, resource: GenomicResource):
        cache_base_path = urlparse(self._cache.get_url()).path
        cache_path = os.path.join(cache_base_path, resource.get_id())
        os.makedirs(cache_path, exist_ok=True)

        def copy_file(filename: str):
            output_path = os.path.join(cache_path, filename)
            with open(output_path, "wb") as destination_file:
                for chunk in resource.get_repo().stream_resource_file(
                        resource.get_id(), filename):
                    destination_file.write(chunk)

        for file in resource.get_manifest().keys():
            copy_file(file)

        GenomicResourcesRepo.create_genomic_resource_repository(
            cache_base_path
        )

        self._cache.reload()

    def cache_resource(self, resource_id: str):
        for repository in self.repositories:
            resource = repository.get_resource(resource_id)
            if resource is not None:
                self._do_cache(resource)
                return
