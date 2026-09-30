"""The collection of gene scores a GPF instance serves."""

from __future__ import annotations

from dataclasses import dataclass

from gain.gene_scores.gene_scores import GeneScore
from gain.genomic_resources.histogram import Histogram


@dataclass
class GeneScoreDesc:
    """Description of a single gene score, as shown by the web interface."""

    resource_id: str
    score_id: str
    column_name: str
    value_type: str

    hist: Histogram
    description: str
    help: str
    small_values_desc: str | None
    large_values_desc: str | None


class GeneScoresDb:
    """Holds the gene scores configured for a GPF instance."""

    def __init__(self, gene_scores: list[GeneScore]):
        self.score_descs: dict[str, GeneScoreDesc] = {}
        self.gene_scores: dict[str, GeneScore] = {}
        for gene_score in gene_scores:
            self.gene_scores[gene_score.resource.get_id()] = gene_score
            for score_desc in GeneScoresDb.build_descs_from_score(gene_score):
                self.score_descs[score_desc.score_id] = score_desc

    @staticmethod
    def build_descs_from_score(
        gene_score: GeneScore,
    ) -> list[GeneScoreDesc]:
        """Build the descriptions of all scores in a gene score resource."""
        return [
            GeneScoreDesc(
                resource_id=gene_score.resource.resource_id,
                score_id=score_id,
                column_name=score_def.column_name,
                value_type=score_def.value_type,
                hist=gene_score.get_score_histogram(score_id),
                description=score_def.desc,
                help=gene_score.build_score_help(score_id),
                small_values_desc=score_def.small_values_desc,
                large_values_desc=score_def.large_values_desc,
            )
            for score_id, score_def in gene_score.score_definitions.items()
        ]

    def get_score_ids(self) -> list[str]:
        """Return the sorted IDs of all scores contained."""
        return sorted(self.score_descs.keys())

    def get_gene_score_ids(self) -> list[str]:
        """Return the sorted resource IDs of all gene scores contained."""
        return sorted(self.gene_scores.keys())

    def get_gene_scores(self) -> list[GeneScore]:
        """Return all the gene scores contained."""
        return list(self.gene_scores.values())

    def get_scores(self) -> list[GeneScoreDesc]:
        """Return the descriptions of all scores contained."""
        return list(self.score_descs.values())

    def get_gene_score(self, score_id: str) -> GeneScore | None:
        """Return the gene score with the given resource ID, if any."""
        if score_id not in self.gene_scores:
            return None
        assert self.gene_scores[score_id].df is not None
        return self.gene_scores[score_id]

    def get_score_desc(self, score_id: str) -> GeneScoreDesc | None:
        """Return the description of the given score, if any."""
        return self.score_descs.get(score_id)

    def __getitem__(self, score_id: str) -> GeneScoreDesc:
        if score_id not in self.score_descs:
            raise ValueError(f"score {score_id} not found")
        return self.score_descs[score_id]

    def __contains__(self, score_id: str) -> bool:
        return score_id in self.score_descs

    def __len__(self) -> int:
        return len(self.score_descs)
