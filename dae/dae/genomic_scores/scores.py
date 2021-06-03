from typing import Dict, List, Union


class GenomicScore:
    def __init__(self, config):
        self.config = config
        self.id: str = config.id
        self.name: str = config.name
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
        self.children: Dict[str, Union[GenomicScore, "GenomicScoreGroup"]] = {}

    @property
    def score_children(self) -> List[GenomicScore]:
        result = list()
        for child in self.children.values():
            if isinstance(child, GenomicScore):
                result.append(child)
            elif isinstance(child, GenomicScoreGroup):
                result.extend(child.score_children)
            else:
                # TODO should raise error, disabled temporarily
                # raise TypeError
                result.append(child)
        return result

    def get_genomic_score(self, genomic_score_id: str) -> GenomicScore:
        return next(filter(
            lambda gs: gs.id == genomic_score_id, self.score_children
        ))
