"""Provides caching genomic resources"""
import os
import pathlib
import logging

from typing import Optional, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

import yaml

from .repository import GenomicResource, GR_CONF_FILE_NAME
from .repository import GenomicResourceRepo
from .dir_repository import GenomicResourceDirRepo

logger = logging.getLogger(__name__)


class CachingDirectoryRepo(GenomicResourceDirRepo):

    def __init__(self, repo_id, directory, remote_repo: GenomicResourceRepo):
        super().__init__(repo_id, directory)
        self.remote_repo = remote_repo

    def get_resource(
            self, resource_id, version_constraint=None,
            genomic_repository_id=None) -> Optional[GenomicResource]:

        remote_resource = self.remote_repo.get_resource(
            resource_id, version_constraint)
        if remote_resource is None:
            return None

        resource = super().get_resource(
            resource_id, version_constraint, genomic_repository_id)
        if resource is not None:
            self._refresh_cached_genomic_resource(
                resource, remote_resource)
        else:
            self._save_cached_resource(remote_resource)            
        self.refresh()

        return super().get_resource(
            resource_id, version_constraint, genomic_repository_id)

    def _refresh_cached_genomic_resource(
            self, cached_resource: GenomicResource,
            remote_resource: GenomicResource):
        mnfst_cache = cached_resource.get_manifest()
        mnfst_remote = remote_resource.get_manifest()
        if mnfst_cache == mnfst_remote:
            return

        logger.debug(
            "genomic resource %s needs refresh", remote_resource.resource_id)
        assert cached_resource.repo == self

        self._update_resource(remote_resource)

    def _save_cached_resource(self, resource: GenomicResource):
        manifest = resource.get_manifest()

        cached = GenomicResource(
            resource.resource_id, resource.version, self)
        resource_config_entry = manifest[GR_CONF_FILE_NAME]
        self._copy_manifest_entry(
            cached, resource, resource_config_entry)
        cached.save_manifest(manifest)

    def open_raw_file(self, genomic_resource: GenomicResource, filename: str,
                      mode="rt", uncompress=False, seekable=False):

        full_file_path = self.get_file_path(genomic_resource, filename)
        if "w" not in mode and not full_file_path.exists():
            remote_resource = self.remote_repo.get_resource(
                genomic_resource.resource_id)
            if remote_resource is None:
                raise ValueError(
                    f"remote resource {genomic_resource.resource_id} missing")
            remote_manifest = remote_resource.get_manifest()
            if filename not in remote_manifest:
                raise ValueError(
                    f"remote resource {genomic_resource.resource_id} missing file: "
                    f"{filename}")

            file_remote_entry = remote_manifest[filename]
            self._copy_manifest_entry(
                genomic_resource, remote_resource, file_remote_entry)

        return super().open_raw_file(
            genomic_resource, filename, mode, uncompress, seekable)

    def get_files(self, genomic_resource: GenomicResource):
        for entry in genomic_resource.get_manifest():
            yield entry.name, entry.size, entry.time

    def load_yaml(self, genomic_resource, filename):
        content = self._get_local_file_content(
            genomic_resource, filename, uncompress=True)
        print(content)

        return yaml.safe_load(content)

    def _get_local_file_content(
            self, genomic_resource, filename, uncompress=True, mode="t"):
        """Returns content of a file in given resource"""
        with self.open_raw_file(
                genomic_resource, filename, mode=f"r{mode}",
                uncompress=uncompress) as infile:
            return infile.read()

    def _update_resource(
            self, remote_resource: GenomicResource):

        dest_gr: Optional[GenomicResource] = super().get_resource(
            remote_resource.resource_id,
            f"={remote_resource.get_version_str()}")
        assert dest_gr is not None

        assert dest_gr.repo == self
        dest_manifest = dest_gr.get_manifest()
        src_manifest = remote_resource.get_manifest()

        if dest_manifest == src_manifest:
            logger.debug("nothing to update %s", dest_gr.resource_id)
            return

        manifest_diff = {}
        for dest_file in dest_manifest:
            manifest_diff[dest_file.name] = [dest_file, None]
        for source_file in src_manifest:
            if source_file.name in manifest_diff:
                manifest_diff[source_file.name][1] = source_file
            else:
                manifest_diff[source_file.name] = [None, source_file]

        for dest_file, src_file in manifest_diff.values():

            if dest_file is None:
                continue
            elif dest_file and src_file is None:
                # delete dest_file
                self._delete_manifest_entry(
                    dest_gr, dest_file)

        dest_gr.save_manifest(src_manifest)


class GenomicResourceCachedRepo(GenomicResourceRepo):

    def __init__(self, child, cache_dir):
        repo_id: str = f"{child.repo_id}.caching_repo"
        super().__init__(repo_id)

        logger.debug(
            "creating cached GRR with cache directory: %s", cache_dir)

        self.child: GenomicResourceRepo = child
        self.cache_dir = pathlib.Path(cache_dir)
        self.cache_repos: Dict[str, CachingDirectoryRepo] = {}

    def get_all_resources(self):
        yield from self.child.get_all_resources()

        for cache_repo in self.cache_repos.values():
            yield from cache_repo.get_all_resources()

    def _get_or_create_cache_dir_repo(self, repo) -> CachingDirectoryRepo:
        repo_id = repo.repo_id
        if repo_id not in self.cache_repos:
            cached_repo_dir = self.cache_dir / repo_id
            logger.debug(
                "going to create cached repo directory: %s", cached_repo_dir)
            os.makedirs(cached_repo_dir, exist_ok=True)
            self.cache_repos[repo_id] = \
                CachingDirectoryRepo(
                    f"{repo_id}.cached", cached_repo_dir, repo)

        cached_repo = self.cache_repos[repo_id]
        assert cached_repo.repo_id == f"{repo_id}.cached"
        return cached_repo

    def get_resource(self, resource_id, version_constraint=None,
                     genomic_repository_id=None) -> Optional[GenomicResource]:

        gr_child = self.child.get_resource(
            resource_id, version_constraint, genomic_repository_id)

        if not gr_child:
            return None

        cached_repo = self._get_or_create_cache_dir_repo(gr_child.repo)

        exact_version_constraint = f"={gr_child.get_version_str()}"
        return cached_repo.get_resource(
            resource_id, exact_version_constraint)

    def cache_resources(
        self, workers=4,
        resources: Optional[list[str]] = None
    ):
        """Caches all resources from a list of remote resource IDs"""
        executor = ThreadPoolExecutor(max_workers=workers)
        futures = []

        if resources is None:
            grs = self.child.get_all_resources()
        else:
            grs = []
            for resource_id in resources:
                r = self.child.get_resource(resource_id)
                assert r is not None, resource_id
                grs.append(r)

        for gr_child in grs:
            cached_repo = self._get_or_create_cache_dir_repo(gr_child.repo)
            futures.append(
                executor.submit(cached_repo.store_resource, gr_child)
            )
        for future in as_completed(futures):
            future.result()
