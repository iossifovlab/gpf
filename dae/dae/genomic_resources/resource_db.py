import logging

from typing import Optional

from urllib.parse import urlparse
from dae.genomic_resources.resources import GenomicResource
from dae.genomic_resources.repository import GenomicResourcesRepo, \
    FSGenomicResourcesRepo, \
    HTTPGenomicResourcesRepo, GenomicResourcesRepoCache


logger = logging.getLogger(__name__)


class GenomicResourceDB:

    def __init__(self, repositories_config):
        self.repositories = {}
        for repo_conf in repositories_config:
            repo_id = repo_conf["id"]
            repo_url = urlparse(repo_conf["url"])
            repo_cache = repo_conf.get("cache")

            logger.info(f"going to create repository from: {repo_url}")
            if repo_url.scheme == "file":
                repo = FSGenomicResourcesRepo(repo_id, repo_url.path)
                repo.load()
            elif repo_url.scheme == "http":
                repo = HTTPGenomicResourcesRepo(repo_id, repo_url.geturl())
                repo.load()
            if repo_cache is not None:
                repo = GenomicResourcesRepoCache(repo, repo_cache)
            self.repositories[repo_id] = repo

    def get_repository(self, repo_id: str) -> Optional[GenomicResourcesRepo]:
        return self.repositories.get(repo_id)

    def get_resource(
        self, resource_id: str, repo_id: str = None
    ) -> Optional[GenomicResource]:

        if repo_id is not None:
            repository = self.repositories.get(repo_id)
            if repository is None:
                return None
            return repository.get_resource(resource_id)
        else:
            for repository in self.repositories.values():
                resource = repository.get_resource(resource_id)
                if resource is not None:
                    return resource

            return None
