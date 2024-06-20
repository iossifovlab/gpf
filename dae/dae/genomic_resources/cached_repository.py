"""Provides caching genomic resources."""
from __future__ import annotations

import logging
import os
from collections.abc import Generator, Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import IO, Any, Optional, Union

import pysam

from dae.genomic_resources.fsspec_protocol import FsspecReadWriteProtocol
from dae.genomic_resources.repository import (
    GR_CONF_FILE_NAME,
    GenomicResource,
    GenomicResourceRepo,
    Manifest,
    ReadOnlyRepositoryProtocol,
    is_version_constraint_satisfied,
)

from .fsspec_protocol import build_fsspec_protocol

logger = logging.getLogger(__name__)


class CacheResource(GenomicResource):
    """Represents resources stored in cache."""

    def __init__(self, resource: GenomicResource, protocol: CachingProtocol):
        super().__init__(
            resource.resource_id,
            resource.version,
            protocol,
            config=resource.config,
            manifest=resource.get_manifest())


class CachingProtocol(ReadOnlyRepositoryProtocol):
    """Defines caching GRR repository protocol."""

    def __init__(
            self,
            remote_protocol: ReadOnlyRepositoryProtocol,
            local_protocol: FsspecReadWriteProtocol):

        super().__init__(local_protocol.proto_id)
        self.remote_protocol = remote_protocol
        self.local_protocol = local_protocol
        self._all_resources: Optional[list[CacheResource]] = None

    def get_url(self) -> str:
        return self.remote_protocol.get_url()

    def invalidate(self) -> None:
        self.remote_protocol.invalidate()
        self.local_protocol.invalidate()
        self._all_resources = None

    def get_all_resources(self) -> Generator[GenomicResource, None, None]:
        if self._all_resources is None:
            self._all_resources = []
            for remote_resource in self.remote_protocol.get_all_resources():
                self._all_resources.append(
                    self._create_cache_resource(remote_resource))
            self.local_protocol.invalidate()
        yield from self._all_resources

    def _create_cache_resource(
            self, remote_resource: GenomicResource) -> CacheResource:

        return CacheResource(
            remote_resource,
            self)

    def refresh_cached_resource_file(
            self, resource: GenomicResource, filename: str) -> tuple[str, str]:
        """Refresh a resource file in cache if neccessary."""
        assert resource.proto == self

        if filename.endswith(".lockfile"):
            # Ignore lockfiles
            return (resource.resource_id, filename)

        remote_resource = self.remote_protocol.get_resource(
            resource.resource_id,
            f"={resource.get_version_str()}")

        # Lock the resource file to avoid caching it simultaneously
        with self.local_protocol.obtain_resource_file_lock(resource, filename):
            self.local_protocol.update_resource_file(
                remote_resource, resource, filename)
        return (resource.resource_id, filename)

    def refresh_cached_resource(self, resource: GenomicResource) -> None:
        """Refresh all resource files in cache if neccessary."""
        assert resource.proto == self

        for entry in resource.get_manifest():
            filename = entry.name
            if filename.endswith(".lockfile"):
                continue
            remote_resource = self.remote_protocol.get_resource(
                resource.resource_id,
                f"={resource.get_version_str()}")

            # Lock the resource file to avoid caching it simultaneously
            with self.local_protocol.obtain_resource_file_lock(
                    resource, filename):
                self.local_protocol.update_resource_file(
                    remote_resource, resource, filename)

    def get_resource_url(self, resource: GenomicResource) -> str:
        """Return url of the specified resources."""
        return self.local_protocol.get_resource_url(resource)

    def get_resource_file_url(
            self, resource: GenomicResource, filename: str) -> str:
        """Return url of a file in the resource."""
        self.refresh_cached_resource_file(resource, filename)
        return self.local_protocol.get_resource_file_url(resource, filename)

    def open_raw_file(
            self, resource: GenomicResource, filename: str,
            mode: str = "rt", **kwargs: Union[str, bool, None]) -> IO:
        if "w" in mode:
            raise OSError(
                f"Read-Only caching protocol {self.get_id()} trying to open "
                f"{filename} for writing")

        self.refresh_cached_resource_file(resource, filename)
        return self.local_protocol.open_raw_file(
            resource, filename, mode, **kwargs)

    def open_tabix_file(
            self, resource: GenomicResource, filename: str,
            index_filename: Optional[str] = None) -> pysam.TabixFile:
        self.refresh_cached_resource_file(resource, filename)
        if index_filename is None:
            index_filename = f"{filename}.tbi"
        self.refresh_cached_resource_file(resource, index_filename)

        return self.local_protocol.open_tabix_file(
            resource, filename, index_filename)

    def open_vcf_file(
            self, resource: GenomicResource, filename: str,
            index_filename: Optional[str] = None) -> pysam.VariantFile:
        self.refresh_cached_resource_file(resource, filename)
        if index_filename is None:
            index_filename = f"{filename}.tbi"
        self.refresh_cached_resource_file(resource, index_filename)

        return self.local_protocol.open_vcf_file(
            resource, filename, index_filename)

    def open_bigwig_file(
            self, resource: GenomicResource, filename: str) -> Any:
        self.refresh_cached_resource_file(resource, filename)
        return self.local_protocol.open_bigwig_file(resource, filename)

    def file_exists(self, resource: GenomicResource, filename: str) -> bool:
        self.refresh_cached_resource_file(resource, filename)

        return self.local_protocol.file_exists(resource, filename)

    def load_manifest(self, resource: GenomicResource) -> Manifest:
        self.refresh_cached_resource_file(resource, GR_CONF_FILE_NAME)
        return self.local_protocol.load_manifest(resource)


class GenomicResourceCachedRepo(GenomicResourceRepo):
    """Defines caching genomic resources repository."""

    def __init__(
            self, child: GenomicResourceRepo, cache_url: str,
            **kwargs: Union[str, None]):
        repo_id: str = f"{child.repo_id}.caching_repo"
        super().__init__(repo_id)

        logger.debug(
            "creating cached GRR with cache url: %s", cache_url)
        self._all_resources: Optional[list[GenomicResource]] = None
        self.child: GenomicResourceRepo = child
        self.cache_url = cache_url
        self.cache_protos: dict[str, CachingProtocol] = {}
        self.additional_kwargs = kwargs

    def invalidate(self) -> None:
        self.child.invalidate()
        for proto in self.cache_protos.values():
            proto.invalidate()

    def get_all_resources(self) -> Generator[GenomicResource, None, None]:
        if self._all_resources is None:
            self._all_resources = []
            for remote_resource in self.child.get_all_resources():
                cache_proto = self._get_or_create_cache_proto(
                    remote_resource.proto)
                version_constraint = f"={remote_resource.get_version_str()}"
                self._all_resources.append(
                    cache_proto.get_resource(
                        remote_resource.resource_id, version_constraint))
        yield from self._all_resources

    def _get_or_create_cache_proto(
            self, proto: ReadOnlyRepositoryProtocol) -> CachingProtocol:
        proto_id = proto.proto_id
        if proto_id not in self.cache_protos:
            cached_proto_url = os.path.join(self.cache_url, proto_id)
            logger.debug(
                "going to create cached protocol with url: %s",
                cached_proto_url)

            cache_proto = build_fsspec_protocol(
                f"{proto_id}.cached",
                cached_proto_url,
                **self.additional_kwargs)
            if not isinstance(cache_proto, FsspecReadWriteProtocol):
                raise ValueError(
                    f"caching protocol should be RW;"
                    f"{cached_proto_url} is not RW")
            self.cache_protos[proto_id] = \
                CachingProtocol(
                    proto,
                    cache_proto)

        return self.cache_protos[proto_id]

    def find_resource(
        self, resource_id: str,
        version_constraint: Optional[str] = None,
        repository_id: Optional[str] = None,
    ) -> Optional[GenomicResource]:
        """Return requested resource or None if not found."""
        matching_resources: list[GenomicResource] = []
        for res in self.get_all_resources():
            if res.resource_id != resource_id:
                continue
            if repository_id is not None and \
                    res.proto.proto_id != repository_id:
                continue
            if is_version_constraint_satisfied(
                    version_constraint, res.version):
                matching_resources.append(res)
        if not matching_resources:
            return None

        def get_resource_version(res: GenomicResource) -> tuple[int, ...]:
            return res.version

        return max(
            matching_resources,
            key=get_resource_version)

    def get_resource(
            self, resource_id: str,
            version_constraint: Optional[str] = None,
            repository_id: Optional[str] = None) -> GenomicResource:

        remote_resource = self.child.get_resource(
            resource_id, version_constraint, repository_id)

        cache_proto = self._get_or_create_cache_proto(
            remote_resource.proto)
        version_constraint = f"={remote_resource.get_version_str()}"
        return cache_proto.get_resource(resource_id, version_constraint)

    def get_resource_cached_files(self, resource_id: str) -> set[str]:
        """Get a set of filenames of cached files for a given resource."""
        resource = self.child.get_resource(resource_id)
        cache_proto = self._get_or_create_cache_proto(
            resource.proto)
        cached_files = set()
        for filename in map(lambda entry: entry.name, resource.get_manifest()):
            if filename == GR_CONF_FILE_NAME:
                continue
            if cache_proto.local_protocol.file_exists(resource, filename):
                cached_files.add(filename)
        return cached_files


def cache_resources(
        repository: GenomicResourceRepo, resource_ids: Optional[Iterable[str]],
        workers: Optional[int] = None) -> None:
    """Cache resources from a list of remote resource IDs."""
    # pylint: disable=import-outside-toplevel
    from dae.genomic_resources import get_resource_implementation_builder

    executor = ThreadPoolExecutor(max_workers=workers)
    futures = []
    if resource_ids is None:
        resources: list[GenomicResource] = \
            list(repository.get_all_resources())
    else:
        resources = []
        for resource_id in resource_ids:
            remote_res = repository.get_resource(resource_id)
            assert remote_res is not None, resource_id
            resources.append(remote_res)

    for resource in resources:
        if not isinstance(resource.proto, CachingProtocol):
            continue

        cached_proto = resource.proto
        impl_builder = get_resource_implementation_builder(resource.get_type())
        if impl_builder is None:
            logger.info(
                "unexpected resource type <%s> for resource %s; "
                "updating resource", resource.get_type(), resource.resource_id)
            futures.append(
                executor.submit(
                    cached_proto.refresh_cached_resource, resource,
                ),
            )
            continue

        futures.append(
            executor.submit(
                cached_proto.refresh_cached_resource_file,  # type: ignore
                resource,
                "genomic_resource.yaml",
            ),
        )
        impl = impl_builder(resource)

        for res_file in impl.files:
            logger.info(
                "request to cache resource file: (%s, %s) from %s",
                resource.resource_id, res_file,
                cached_proto.remote_protocol.proto_id)
            futures.append(
                executor.submit(
                    cached_proto.refresh_cached_resource_file,  # type: ignore
                    resource,
                    res_file,
                ),
            )

    total_files = len(futures)
    logger.info("caching %s files", total_files)
    count = 0
    for future in as_completed(futures):
        filename: str

        resource_id, filename = future.result()  # type: ignore
        count += 1
        logger.info(
            "finished %s/%s (%s: %s)", count, total_files,
            resource_id, filename)

    executor.shutdown()
