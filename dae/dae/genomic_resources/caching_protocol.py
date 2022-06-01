"""Defines caching GRR repository protocol."""

from typing import Generator, Optional

from dae.genomic_resources.repository import \
    ReadOnlyRepositoryProtocol, \
    ReadWriteRepositoryProtocol, \
    GenomicResource, \
    Manifest


class CachingProtocol(ReadOnlyRepositoryProtocol):
    """Defines caching GRR repository protocol."""

    def __init__(
            self,
            proto_id: str,
            remote_protocol: ReadOnlyRepositoryProtocol,
            local_protocol: ReadWriteRepositoryProtocol):

        super().__init__(proto_id)
        self.remote_protocol = remote_protocol
        self.local_protocol = local_protocol

    def get_all_resources(self) -> Generator[GenomicResource, None, None]:
        yield from self.remote_protocol.get_all_resources()

    def get_resource(
            self, resource_id: str,
            version_constraint: Optional[str] = None) -> GenomicResource:

        remote_resource = self.remote_protocol.get_resource(
            resource_id, version_constraint)

        local_resource = self.local_protocol.update_resource(remote_resource)
        return local_resource

    def open_raw_file(self, resource, filename, mode="rt", **kwargs):
        assert resource.repo == self.local_protocol

        return self.local_protocol.open_raw_file(
            resource, filename, mode, **kwargs)

    def open_tabix_file(self, resource, filename, index_filename=None):
        assert resource.repo == self.local_protocol

        return self.local_protocol.open_tabix_file(
            resource, filename, index_filename)

    def file_exists(self, resource, filename) -> bool:
        assert resource.repo == self.local_protocol

        return self.local_protocol.file_exists(resource, filename)

    def load_manifest(self, resource: GenomicResource) -> Manifest:
        return self.local_protocol.load_manifest(resource)
