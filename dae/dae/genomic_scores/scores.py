from typing import Dict, List, Union, NamedTuple


class Field(NamedTuple):
    id: str
    type: str
    desc: str
    idx: int


class Attributes(NamedTuple):
    source: str
    dest: str


class GenomicScore:
    def __init__(self, config):
        self.config = config
        self.id: str = config.id
        self.name: str = config.score_file.name
        self.description: str = config.meta
        self.identification: List[Field] = [
            Field(idf) for idf in config.identification
        ]
        self.scores: List[Field] = [Field(idf) for idf in config.scores]
        self.annotator: str = config.default_annotation.annotator
        self.attributes: List[Attributes] = [
            Attributes(attr) for attr in config.default_annotation.attributes
        ]

    @property
    def fields(self) -> List[Field]:
        return self.identification + self.scores


class GenomicScoreGroup:
    def __init__(self, id: str):
        self.id = id
        self.children: Dict[str, Union[GenomicScore, "GenomicScoreGroup"]] = {}

    @property
    def score_children(self) -> List[GenomicScore]:
        result = list()
        for child in self.children.values():
            if isinstance(child, GenomicScore):
                result.append(child)
            else:
                result.extend(child.score_children)
        return result

    def get_genomic_score(self, genomic_score_id: str) -> GenomicScore:
        return next(filter(
            lambda gs: gs.id == genomic_score_id, self.score_children
        ))
