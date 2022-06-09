"""Provides caching genomic resources."""
import os
import logging

from typing import Iterable, Optional, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

from .repository import GenomicResource, \
    ReadOnlyRepositoryProtocol, ReadWriteRepositoryProtocol
from .repository import GenomicResourceRepoBase, GenomicResourceRepo
from .fsspec_protocol import build_fsspec_protocol
from .caching_protocol import CachingProtocol

logger = logging.getLogger(__name__)


class GenomicResourceCachedRepo(GenomicResourceRepoBase):
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
            remote_resource.protocol)
        version_constraint = f"={remote_resource.get_version_str()}"
        return cache_proto.get_resource(resource_id, version_constraint)

    def get_resource(self, resource_id, version_constraint=None,
                     repository_id=None) -> GenomicResource:

        remote_resource = self.child.get_resource(
            resource_id, version_constraint, repository_id)

        cache_proto = self._get_or_create_cache_proto(
            remote_resource.protocol)
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
                rem_resource.protocol)
            futures.append(
                executor.submit(cached_proto.cache_resource, rem_resource)
            )
        for future in as_completed(futures):
            future.result()
