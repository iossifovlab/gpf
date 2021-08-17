import os
import pysam

from urllib.parse import urlparse
from typing import Dict, List, Tuple, Union


GenomicScoreChild = Union["GenomicResource", "GenomicResourceGroup"]
ParentsScoreTuple = Tuple[List["GenomicResourceGroup"], "GenomicResource"]


class GenomicResourceBase:
    def get_id(self):
        return self._id

    def get_url(self):
        raise NotImplementedError

    def get_children(self):
        raise NotImplementedError

    def get_repo(self):
        return self._repo


class GenomicResource(GenomicResourceBase):
    def __init__(self, config, url, manifest, repo):
        # import traceback as tb
        # tb.print_stack()
        print("\n", 80*"=", sep="")
        print("\nconfig\t:", config, "\nurl\t:", url)

        self._config = config
        self._url = url
        self._repo = repo
        self._manifest = manifest
        self._id: str = config.id
        self._score_type = config.score_type
        self._description: str = config.meta

    def get_url(self):
        return self._url

    def get_children(self):
        return [self]

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
    def __init__(self, id: str, url: str):
        self._id = id
        self._url = url
        self.children: Dict[str, GenomicResourceBase] = {}

    def get_url(self):
        return self._url

    def get_resources(self):
        result = []
        for child in self.children.values():
            result.extend(child.get_children())
        return result

    def get_children(self):
        return list(self.children.values())

    def add_child(self, resource):
        self.children[resource.get_id()] = resource

    def resource_children(
        self, parents: List["GenomicResourceGroup"] = None
    ) -> List[ParentsScoreTuple]:
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
    ) -> Union[ParentsScoreTuple, Tuple[None, None]]:
        for parents, genomic_resource in self.resource_children():
            if genomic_resource.id == genomic_resource_id:
                return parents, genomic_resource
        return None, None
