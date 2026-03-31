from typing import Any


class GPStatistic:
    """
    Class representing GP statistics.

    Used as a medium between the DB and the API.
    """

    def __init__(
        self, gene_symbol: str,
        gene_sets: list[str],
        gene_scores: dict,
        variant_counts: dict,
    ):
        self.gene_symbol = gene_symbol
        self.gene_sets = gene_sets
        self.gene_scores = gene_scores
        self.variant_counts = variant_counts

    def _scores_to_json(self) -> list[dict[str, Any]]:
        result = []
        for category_id, scores in self.gene_scores.items():
            subresult = {"id": category_id, "scores": []}
            for score_id, score in scores.items():
                subresult["scores"].append({"id": score_id, **score})
            result.append(subresult)
        return result

    def _variant_counts_to_json(self) -> list[dict[str, Any]]:
        result = []
        for study_id, counts in self.variant_counts.items():
            subresult = {"id": study_id, "personSets": []}
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

    def to_json(self) -> dict[str, Any]:
        return {
            "geneSymbol": self.gene_symbol,
            "geneSets": self.gene_sets,
            "geneScores": self._scores_to_json(),
            "studies": self._variant_counts_to_json(),
        }
