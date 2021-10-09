from .repository import GenomicResourceRepo
from .repository import GenomicResource


class GenomicResourceGroupRepo(GenomicResourceRepo):
    def __init__(self, children):
        self.children = children

    def get_all_resources(self):
        for chRepo in self.children:
            for gr in chRepo.get_all_resources():
                yield gr

    def get_resource(self, resource_id, version_constraint=None,
                     genomic_repository_id=None) -> GenomicResource:
        for chRepo in self.children:
            gr = chRepo.get_resource(
                resource_id, version_constraint, genomic_repository_id)
            if gr:
                return gr
        return None
