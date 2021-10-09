from .repository import GenomicResource
from .repository import GenomicResourceRepo
from .dir_repository import GenomicResourceDirRepo

import pathlib
import shutil
import os


class GenomicResourceCachedRepo(GenomicResourceRepo):
    def __init__(self, child, cacheDir):
        self.child = child
        self.cacheDir = pathlib.Path(cacheDir)
        self.cacheRepos = {}

    def get_all_resources(self):
        yield from self.child.get_all_resources()

    def _get_or_create_chache_dir_repo(self, repo_id):
        if repo_id not in self.cacheRepos:
            cached_repo_dir = self.cacheDir / repo_id
            os.makedirs(cached_repo_dir, exist_ok=True)
            self.cacheRepos[repo_id] = GenomicResourceDirRepo(
                repo_id, directory=cached_repo_dir)
        cached_repo = self.cacheRepos[repo_id]
        assert cached_repo.id == repo_id
        return cached_repo

    def get_resource(self, resource_id, version_constraint=None,
                     genomic_repository_id=None) -> GenomicResource:
        grChld = self.child.get_resource(
            resource_id, version_constraint, genomic_repository_id)
        if not grChld:
            return None

        cached_repo = self._get_or_create_chache_dir_repo(grChld.repo.id)

        exact_version_constraint = "=" + grChld.get_version_str()
        grCache = cached_repo.get_resource(
            resource_id, exact_version_constraint)
        if grCache:
            self.refresh_cached_genomic_resource(grCache, grChld)
        else:
            cached_repo.store_resource(grChld)
        return cached_repo.get_resource(resource_id,
                                        exact_version_constraint)

    def refresh_cached_genomic_resource(self, cached: GenomicResource,
                                        childs: GenomicResource):
        mnfstCache = cached.get_manifest()
        mnfstChld = childs.get_manifest()
        if mnfstCache == mnfstChld:
            return
        shutil.rmtree(cached.repo.directory /
                      cached.get_genomic_resource_dir())
        cached.repo.store_resource(childs)
