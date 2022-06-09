"""Defines caching GRR repository protocol."""
from __future__ import annotations

from typing import Generator, Optional

from dae.genomic_resources.repository import \
    GR_CONF_FILE_NAME, \
    ReadOnlyRepositoryProtocol, \
    ReadWriteRepositoryProtocol, \
    GenomicResource, \
    Manifest


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
            cache_protocol: ReadWriteRepositoryProtocol):

        super().__init__(cache_protocol.proto_id)
        self.remote_protocol = remote_protocol
        self.local_protocol = cache_protocol

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
        assert resource.protocol == self

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
