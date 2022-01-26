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

    def _scores_to_json(self, score_categories):
        result = list()
        for category_id, scores in score_categories.items():
            subresult = {"id": category_id, "scores": list()}
            for score_id, score in scores.items():
                subresult["scores"].append({"id": score_id, **score})
            result.append(subresult)
        return result

    def _variant_counts_to_json(self, variant_counts):
        result = list()
        for study_id, counts in variant_counts.items():
            subresult = {"id": study_id, "personSets": list()}
            for person_set_id, count in counts.items():
                subresult["personSets"].append({
                    "id": person_set_id,
                    "effectTypes": [
                        {"id": efftype, "value": value}
                        for efftype, value in count.items()
                    ],
                })
            result.append(subresult)
        return result

    def to_json(self):
        return {
            "geneSymbol": self.gene_symbol,
            "geneSets": self.gene_sets,
            "genomicScores": self._scores_to_json(self.genomic_scores),
            "studies": self._variant_counts_to_json(self.variant_counts)
        }