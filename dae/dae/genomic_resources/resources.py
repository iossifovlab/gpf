import os
import pysam

from urllib.parse import urlparse
from typing import Dict, List, Optional, Tuple, Union


ParentsResourceTuple = Tuple[List["GenomicResourceGroup"], "GenomicResource"]


class GenomicResourceBase:
    def __init__(self, resource_id, repo):
        self.resource_id = resource_id
        self.repo = repo

    def get_id(self):
        return self.resource_id

    def get_url(self):
        return os.path.join(self.repo.get_url(), self.get_id())

    def get_path(self):
        return os.path.join(self.repo.get_path(), self.get_id())

    def get_children(self, deep=False):
        return []

    def get_repo(self):
        return self._repo


class GenomicResource(GenomicResourceBase):
    def __init__(self, config, url=None, manifest=None, repo=None):
        # import traceback as tb
        # tb.print_stack()
        print("\n", 80*"=", sep="")
        print("\nconfig\t:", config, "\nurl\t:", url)

        self._config = config
        super(GenomicResource, self).__init__(config["id"], repo)

        self._id: str = config["id"]

    def __repr__(self):
        return f"GR({self._id})"

    def get_config(self):
        return self._config

    def get_manifest(self):
        return self._manifest

    def binary_stream(self, filename, offset=None, size=None):
        return self._repo.stream_resource_file(
            self._id, filename, offset, size
        )

    def tabix_access(self, filename, index_filename=None):
        parse_result = urlparse(self._url)
        if parse_result.scheme == "file":
            filename = os.path.join(parse_result.path, filename)
            if index_filename is not None:
                index_filename = \
                    os.path.join(parse_result.path, index_filename)
        else:
            filename = f"{self._url}/{filename}"
            if index_filename is not None:
                index_filename = f"{self._url}/{filename}"
        return pysam.TabixFile(filename, index=index_filename)

    def open(self):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

    @classmethod
    def get_config_schema(cls):
        raise NotImplementedError


class GenomicResourceGroup(GenomicResourceBase):
    def __init__(self, resource_id: str, url=None, repo=None):
        super(GenomicResourceGroup, self).__init__(resource_id, repo)

        self.children: Dict[str, GenomicResourceBase] = {}

    def __repr__(self):
        return f"GRGroup({self.get_id()})"

    def get_resources(self):
        result = []
        for child in self.children.values():
            result.extend(child.get_children())
        return result

    def get_resource(
        self, resource_id: str, deep=True
    ) -> Optional[GenomicResourceBase]:

        if not deep:
            return self.children.get(resource_id)

        for child in self.get_children(deep=deep):
            if child.get_id() == resource_id:
                return child
        return None

    def get_children(self, deep=False) -> List[GenomicResourceBase]:
        if not deep:
            return list(self.children.values())
        result = []
        for child in self.children.values():
            result.append(child)
            result.extend(child.get_children(deep=True))
        return result

    def add_child(self, resource):
        self.children[resource.get_id()] = resource

    def resource_children(
        self, parents: List["GenomicResourceGroup"] = None
    ) -> List[ParentsResourceTuple]:
        result = list()
        if parents is None:
            parents = [self]
        for child in self.children.values():
            if isinstance(child, GenomicResource):
                result.append((parents, child))
            elif isinstance(child, GenomicResourceGroup):
                result.extend(child.resource_children([*parents, child]))
            else:
                # TODO should raise error, disabled temporarily for HTTP repos
                # raise TypeError
                result.append((parents, child))
        return result

    def get_genomic_resource(
        self, genomic_resource_id: str
    ) -> Union[ParentsResourceTuple, Tuple[None, None]]:
        for parents, genomic_resource in self.resource_children():
            if genomic_resource.get_id() == genomic_resource_id:
                return parents, genomic_resource
        return None, None

    def get_genomic_resources(self):
        for child in self.get_children(deep=True):
            if isinstance(child, GenomicResource):
                yield child
