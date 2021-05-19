class AGPStatistic:
    def __init__(self, gene_symbol, gene_sets, genomic_scores, variant_counts):
        self.gene_symbol = gene_symbol
        self.gene_sets = gene_sets
        self.genomic_scores = genomic_scores
        self.variant_counts = variant_counts

    def to_json(self):
        return {
            "geneSymbol": self.gene_symbol,
            "geneSets": self.gene_sets,
            "genomicScores": self.genomic_scores,
            "studies": self.variant_counts,
        }
