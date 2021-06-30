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
        return self


class GenomicResource(GenomicResourceBase):
    def __init__(self, config, url, manifest, repo):
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

    def score_children(
        self, parents: List["GenomicResourceGroup"] = None
    ) -> List[ParentsScoreTuple]:
        result = list()
        if parents is None:
            parents = [self]
        for child in self.children.values():
            if isinstance(child, GenomicResource):
                result.append((parents, child))
            elif isinstance(child, GenomicResourceGroup):
                result.extend(child.score_children([*parents, child]))
            else:
                # TODO should raise error, disabled temporarily for HTTP repos
                # raise TypeError
                result.append((parents, child))
        return result

    def get_genomic_score(
        self, genomic_score_id: str
    ) -> Union[ParentsScoreTuple, Tuple[None, None]]:
        for parents, genomic_score in self.score_children():
            if genomic_score.id == genomic_score_id:
                return parents, genomic_score
        return None, None
