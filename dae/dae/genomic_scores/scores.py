from typing import Dict, List, Tuple, Union
from dae.annotation.tools.annotator_config import AnnotationConfigParser


GenomicScoreChild = Union["GenomicScore", "GenomicScoreGroup"]
ParentsScoreTuple = Tuple[List["GenomicScoreGroup"], "GenomicScore"]


class GenomicScore:
    def __init__(self, conf_path):
        config = AnnotationConfigParser.load_annotation_config(conf_path)
        self.config = config
        self.conf_path = conf_path
        self.id: str = config.id
        self.name: str = config.name
        self.score_type = config.score_type
        self.filename: str = config.filename
        self.index_file = config.index_file
        self.description: str = config.meta
        self.chrom = config.chrom
        self.pos_begin = config.pos_begin
        self.pos_end = config.pos_end
        self.scores = config.scores
        self.score_type: str = config.score_type
        if config.default_annotation:
            self.attributes = config.default_annotation.attributes
        else:
            self.attributes = None

    @property
    def fields(self):
        return [self.chrom, self.pos_begin, self.pos_end, *self.scores]


class GenomicScoreGroup:
    def __init__(self, id: str):
        self.id = id
        self.children: Dict[str, GenomicScoreChild] = {}

    def score_children(
        self, parents: List["GenomicScoreGroup"] = None
    ) -> List[ParentsScoreTuple]:
        result = list()
        if parents is None:
            parents = [self]
        for child in self.children.values():
            if isinstance(child, GenomicScore):
                result.append((parents, child))
            elif isinstance(child, GenomicScoreGroup):
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
