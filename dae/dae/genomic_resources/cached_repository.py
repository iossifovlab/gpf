"""Provides caching genomic resources"""
import os
import pathlib
import logging

from typing import Optional, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

import pysam

from .repository import GenomicResource, GR_CONF_FILE_NAME
from .repository import GenomicResourceRepo
from .dir_repository import GenomicResourceDirRepo

logger = logging.getLogger(__name__)


class CachingDirectoryRepo(GenomicResourceDirRepo):
    """Provides helper caching directory class for caching repository."""
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
        self.save_manifest(cached, manifest)

    def _copy_or_update_local_file(
            self, local_resource: GenomicResource, filename: str):
        remote_resource = self.remote_repo.get_resource(
            local_resource.resource_id)
        if remote_resource is None:
            raise ValueError(
                f"remote resource {local_resource.resource_id} missing")
        remote_manifest = remote_resource.get_manifest()
        if filename not in remote_manifest:
            raise FileNotFoundError(
                f"remote resource {local_resource.resource_id} missing file: "
                f"{filename}")

        file_remote_entry = remote_manifest[filename]
        self._copy_manifest_entry(
            local_resource, remote_resource, file_remote_entry)

        full_file_path = self._get_file_path(local_resource, filename)
        assert full_file_path.exists()

        return full_file_path

    def file_local(self, genomic_resource, filename):
        """
        Check if a given file in a given resource can be accessed locally
        If inaccessible, it caches the file from the remote repository
        """
        full_file_path = self._get_file_path(genomic_resource, filename)
        if not full_file_path.exists():
            self._copy_or_update_local_file(genomic_resource, filename)
        return True

    def open_raw_file(
            self, resource: GenomicResource, filename: str,
            mode="rt", uncompress=False, seekable=False):

        if "w" not in mode:
            self._copy_or_update_local_file(resource, filename)

        return super().open_raw_file(
            resource, filename, mode, uncompress, seekable)

    def open_tabix_file(self, resource,  filename,
                        index_filename=None):

        full_file_path = self._copy_or_update_local_file(
            resource, filename)

        if not index_filename:
            index_filename = f"{filename}.tbi"
        full_index_path = self._copy_or_update_local_file(
            resource, index_filename)

        return pysam.TabixFile(  # pylint: disable=no-member
            full_file_path, index=full_index_path)

    def get_files(self, resource: GenomicResource):
        for entry in resource.get_manifest():
            yield entry.name, entry.size, entry.time

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

            if dest_file and src_file is None:
                # delete dest_file
                self._delete_manifest_entry(
                    dest_gr, dest_file)

        self.save_manifest(dest_gr, src_manifest)


class GenomicResourceCachedRepo(GenomicResourceRepo):
    """Defines caching genomic resources repository."""

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

        remote_resource = self.child.get_resource(
            resource_id, version_constraint, genomic_repository_id)

        if not remote_resource:
            return None

        cached_repo = self._get_or_create_cache_dir_repo(remote_resource.repo)
        version_constraint = f"={remote_resource.get_version_str()}"
        return cached_repo.get_resource(resource_id, version_constraint)

    def cache_resources(
        self, workers=4,
        resource_ids: Optional[list[str]] = None
    ):
        """Caches all resources from a list of remote resource IDs"""
        executor = ThreadPoolExecutor(max_workers=workers)
        futures = []

        if resource_ids is None:
            resources = self.child.get_all_resources()
        else:
            resources = []
            for resource_id in resource_ids:
                remote_res = self.child.get_resource(resource_id)
                assert remote_res is not None, resource_id
                resources.append(remote_res)

        for rem_resource in resources:
            cached_repo = self._get_or_create_cache_dir_repo(rem_resource.repo)
            futures.append(
                executor.submit(cached_repo.store_resource, rem_resource)
            )
        for future in as_completed(futures):
            future.result()
