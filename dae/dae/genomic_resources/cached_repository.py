"""Provides caching genomic resources."""
from __future__ import annotations
import os
import logging

from typing import Iterable, Optional, Dict, Generator
from concurrent.futures import ThreadPoolExecutor, as_completed

from .repository import GenomicResource, \
    ReadOnlyRepositoryProtocol, ReadWriteRepositoryProtocol
from .repository import AbstractGenomicResourceRepo, GenomicResourceRepo, \
    GR_CONF_FILE_NAME, Manifest
from .fsspec_protocol import build_fsspec_protocol

logger = logging.getLogger(__name__)


class CacheResource(GenomicResource):

    def __init__(self, resource, protocol: CachingProtocol):
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
            local_protocol: ReadWriteRepositoryProtocol):

        super().__init__(local_protocol.proto_id)
        self.remote_protocol = remote_protocol
        self.local_protocol = local_protocol

    def invalidate(self):
        self.remote_protocol.invalidate()
        self.local_protocol.invalidate()

    def get_all_resources(self) -> Generator[GenomicResource, None, None]:
        for remote_resource in self.remote_protocol.get_all_resources():
            yield CacheResource(remote_resource, self)

    def get_resource(
            self, resource_id: str,
            version_constraint: Optional[str] = None) -> GenomicResource:

        remote_resource = self.remote_protocol.get_resource(
            resource_id, version_constraint)
        local_resource = self.local_protocol.get_or_create_resource(
            remote_resource.resource_id, remote_resource.version)

        self.local_protocol.update_resource_file(
            remote_resource, local_resource, GR_CONF_FILE_NAME)
        self.local_protocol.invalidate()

        return CacheResource(
            self.local_protocol.get_resource(
                remote_resource.resource_id,
                f"={remote_resource.get_version_str()}"),
            self)

    def _refresh_resource_file(
            self, resource: GenomicResource, filename: str) -> None:
        assert resource.proto == self

        remote_resource = self.remote_protocol.get_resource(
            resource.resource_id,
            f"={resource.get_version_str()}")

        self.local_protocol.update_resource_file(
            remote_resource, resource, filename)

    def open_raw_file(self, resource, filename, mode="rt", **kwargs):
        if "w" in mode:
            raise IOError(
                f"Read-Only caching protocol {self.get_id()} trying to open "
                f"{filename} for writing")

        self._refresh_resource_file(resource, filename)
        return self.local_protocol.open_raw_file(
            resource, filename, mode, **kwargs)

    def open_tabix_file(self, resource, filename, index_filename=None):
        self._refresh_resource_file(resource, filename)
        if index_filename is None:
            index_filename = f"{filename}.tbi"
        self._refresh_resource_file(resource, index_filename)

        return self.local_protocol.open_tabix_file(
            resource, filename, index_filename)

    def file_exists(self, resource, filename) -> bool:
        self._refresh_resource_file(resource, filename)

        return self.local_protocol.file_exists(resource, filename)

    def load_manifest(self, resource: GenomicResource) -> Manifest:
        self._refresh_resource_file(resource, GR_CONF_FILE_NAME)

        return self.local_protocol.load_manifest(resource)

    def cache_resource(self, resource) -> None:
        self.local_protocol.update_resource(resource)


class GenomicResourceCachedRepo(AbstractGenomicResourceRepo):
    """Defines caching genomic resources repository."""

    def __init__(self, child, cache_url, **kwargs):
        repo_id: str = f"{child.repo_id}.caching_repo"
        super().__init__(repo_id)

        logger.debug(
            "creating cached GRR with cache url: %s", cache_url)

        self.child: GenomicResourceRepo = child
        self.cache_url = cache_url
        self.cache_protos: Dict[str, CachingProtocol] = {}
        self.additional_kwargs = kwargs

    def invalidate(self):
        self.child.invalidate()
        for proto in self.cache_protos.values():
            proto.invalidate()

    def get_all_resources(self):
        for cache_proto in self.cache_protos.values():
            yield from cache_proto.get_all_resources()

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
            if not isinstance(cache_proto, ReadWriteRepositoryProtocol):
                raise ValueError(
                    f"caching protocol should be RW;"
                    f"{cached_proto_url} is not RW")
            self.cache_protos[proto_id] = \
                CachingProtocol(
                    proto,
                    cache_proto)

        return self.cache_protos[proto_id]

    def find_resource(
            self, resource_id, version_constraint=None,
            repository_id=None) -> Optional[GenomicResource]:

        remote_resource = self.child.find_resource(
            resource_id, version_constraint, repository_id)
        if remote_resource is None:
            return None

        cache_proto = self._get_or_create_cache_proto(
            remote_resource.proto)
        version_constraint = f"={remote_resource.get_version_str()}"
        return cache_proto.get_resource(resource_id, version_constraint)

    def get_resource(self, resource_id, version_constraint=None,
                     repository_id=None) -> GenomicResource:

        remote_resource = self.child.get_resource(
            resource_id, version_constraint, repository_id)

        cache_proto = self._get_or_create_cache_proto(
            remote_resource.proto)
        version_constraint = f"={remote_resource.get_version_str()}"
        return cache_proto.get_resource(resource_id, version_constraint)

    def cache_resources(
        self, workers=4,
        resource_ids: Optional[list[str]] = None
    ):
        """Cache resources from a list of remote resource IDs."""
        executor = ThreadPoolExecutor(max_workers=workers)
        futures = []

        if resource_ids is None:
            resources: Iterable[GenomicResource] = \
                self.child.get_all_resources()
        else:
            resources = []
            for resource_id in resource_ids:
                remote_res = self.child.get_resource(resource_id)
                assert remote_res is not None, resource_id
                resources.append(remote_res)

        for rem_resource in resources:
            cached_proto = self._get_or_create_cache_proto(
                rem_resource.proto)
            futures.append(
                executor.submit(cached_proto.cache_resource, rem_resource)
            )
        for future in as_completed(futures):
            future.result()
