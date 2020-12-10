class AGPStatistic:
    def __init__(
            self, gene_symbol, gene_sets, protection_scores,
            autism_scores, variant_counts):
        self.gene_symbol = gene_symbol
        self.gene_sets = gene_sets
        self.protection_scores = protection_scores
        self.autism_scores = autism_scores
        self.variant_counts = variant_counts
