from typing import List
from dae.genomic_resources.score_resources.score_resource import \
    GenomicScoresResource


class FrequencyScoreResource(GenomicScoresResource):
    def open(self):
        pass

    def close(self):
        pass

    def fetch_scores(
        chrom: str, position: int, ref: str, alt: str, scores: List[str]
    ):
        pass
