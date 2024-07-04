"""Provides group genomic resources repository."""

from collections.abc import Generator

from .repository import GenomicResource, GenomicResourceRepo


class GenomicResourceGroupRepo(GenomicResourceRepo):
    """Defines group genomic resources repository."""

    def __init__(
            self, children: list[GenomicResourceRepo],
            repo_id: str | None = None):
        if repo_id is None:
            repo_id = "group_repo"
        super().__init__(repo_id)

        self.children = children

    def invalidate(self) -> None:
        for child in self.children:
            child.invalidate()

    def get_all_resources(self) -> Generator[GenomicResource, None, None]:
        for child_repo in self.children:
            yield from child_repo.get_all_resources()

    def find_resource(
            self, resource_id: str, version_constraint: str | None = None,
            repository_id: str | None = None) -> GenomicResource | None:

        for child_repo in self.children:
            if repository_id is not None and \
                    child_repo.repo_id is not None and \
                    child_repo.repo_id != resource_id:
                continue
            res = child_repo.find_resource(
                resource_id, version_constraint)
            if res:
                return res

        return None

    def get_resource(
            self, resource_id: str, version_constraint: str | None = None,
            repository_id: str | None = None) -> GenomicResource:

        for child_repo in self.children:
            if repository_id is not None and \
                    child_repo.repo_id is not None and \
                    child_repo.repo_id != resource_id:
                continue
            res = child_repo.find_resource(
                resource_id, version_constraint, repository_id)
            if res:
                return res
        raise ValueError(
            f"resource {resource_id} {version_constraint} "
            f"({repository_id}) not found")
