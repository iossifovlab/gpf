from typing import List
from dae.genomic_resources.score_resources.score_resource import \
    GenomicScoresResource


class NPScoreResource(GenomicScoresResource):
    def open(self):
        pass

    def close(self):
        pass

    def fetch_scores(chrom: str, position: int, nt: str, scores: List[str]):
        pass

    def fetch_scores_agg(
        chrom: str, pos_begin: int, pos_end: int,
        scores_aggregators
    ):
        pass
