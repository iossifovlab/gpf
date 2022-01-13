from typing import List


class AGPStatistic:
    def __init__(
        self, gene_symbol: str,
        gene_sets: List[str],
        genomic_scores: dict,
        variant_counts: dict,
    ):
        self.gene_symbol = gene_symbol
        self.gene_sets = gene_sets
        self.genomic_scores = genomic_scores
        self.variant_counts = variant_counts
