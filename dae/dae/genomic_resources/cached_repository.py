import os
import pathlib
import logging

from typing import Optional, cast
from concurrent.futures import ThreadPoolExecutor

from .repository import GenomicResource
from .repository import GenomicResourceRepo
from .dir_repository import GenomicResourceDirRepo

logger = logging.getLogger(__name__)


class GenomicResourceCachedRepo(GenomicResourceRepo):
    def __init__(self, child, cache_dir):
        logger.debug(
            f"creating cached GRR with cache directory: {cache_dir}")

        self.child = child
        self.cache_dir = pathlib.Path(cache_dir)
        self.cache_repos = {}

    def get_all_resources(self):
        yield from self.child.get_all_resources()

        for cache_repo in self.cache_repos.values():
            yield from cache_repo.get_all_resources()

    def _get_or_create_cache_dir_repo(self, repo_id):
        if repo_id not in self.cache_repos:
            cached_repo_dir = self.cache_dir / repo_id
            logger.debug(
                f"going to create cached repo directory: {cached_repo_dir}")
            os.makedirs(cached_repo_dir, exist_ok=True)
            self.cache_repos[repo_id] = \
                GenomicResourceDirRepo(f"{repo_id}.cached", cached_repo_dir)
        cached_repo = self.cache_repos[repo_id]
        assert cached_repo.repo_id == f"{repo_id}.cached"
        return cached_repo

    def get_resource(self, resource_id, version_constraint=None,
                     genomic_repository_id=None) -> Optional[GenomicResource]:
        gr_child = self.child.get_resource(
            resource_id, version_constraint, genomic_repository_id)

        if not gr_child:
            return None

        cached_repo = self._get_or_create_cache_dir_repo(
            gr_child.repo.repo_id)

        exact_version_constraint = "=" + gr_child.get_version_str()
        gr_cache = cached_repo.get_resource(
            resource_id, exact_version_constraint)
        if gr_cache:
            self.refresh_cached_genomic_resource(gr_cache, gr_child)
        else:
            cached_repo.store_resource(gr_child)
        return cached_repo.get_resource(resource_id,
                                        exact_version_constraint)

    def cache_all_resources(self, download_limit=4):
        executor = ThreadPoolExecutor(max_workers=download_limit)
        futures = []
        for gr_child in self.child.get_all_resources():
            cached_repo = self._get_or_create_cache_dir_repo(
                    gr_child.repo.repo_id
            )
            futures.append(
                executor.submit(cached_repo.store_resource, gr_child)
            )
        for future in futures:
            future.result()

    def refresh_cached_genomic_resource(self, cached: GenomicResource,
                                        child: GenomicResource):
        mnfst_cache = cached.get_manifest()
        mnfst_child = child.get_manifest()
        if mnfst_cache == mnfst_child:
            return

        cached_repo = cast(GenomicResourceDirRepo, cached.repo)
        cached_repo.update_resource(child)
