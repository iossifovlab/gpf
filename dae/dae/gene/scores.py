from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Union, Any, Optional

from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.genomic_scores import build_score_from_resource
from dae.genomic_resources.histogram import NumberHistogram, \
    CategoricalHistogram, NullHistogram, Histogram
from dae.annotation.annotation_pipeline import AnnotatorInfo


logger = logging.getLogger(__name__)


@dataclass
class ScoreDesc:
    """Data class to describe genomic scores in GenomicScoresDb."""

    resource_id: str
    score_id: str
    source: str
    name: str
    hist: Optional[Union[NumberHistogram, CategoricalHistogram, NullHistogram]]
    description: str
    help: str

    def to_json(self) -> dict[str, Any]:
        hist_data = None
        if self.hist is not None:
            hist_data = self.hist.to_dict()
        return {
            "resource_id": self.resource_id,
            "score_id": self.score_id,
            "source": self.source,
            "name": self.name,
            "hist": hist_data,
            "description": self.description,
            "help": self.help
        }

    @staticmethod
    def from_json(data: dict[str, Any]) -> ScoreDesc:
        """Build a ScoreDesc from a JSON."""
        hist_data: Optional[Histogram] = None
        if "hist" in data:
            hist_type = data["hist"]["config"]["type"]
            if hist_type == "categorical":
                hist_data = CategoricalHistogram.from_dict(data["hist"])
            elif hist_type == "null":
                hist_data = NullHistogram.from_dict(data["hist"])
            elif hist_type == "number":
                hist_data = NumberHistogram.from_dict(data["hist"])
            else:
                raise ValueError(f"Unknown histogram type {hist_type}")
        return ScoreDesc(
            data["resource_id"],
            data["score_id"],
            data["source"],
            data["name"],
            hist_data,
            data["description"],
            data["help"]

        )


class GenomicScoresDb:
    """Genomic scores DB allowing access to genomic scores histograms."""

    def __init__(
            self, grr: GenomicResourceRepo,
            score_annotators: list[AnnotatorInfo]):
        self.grr = grr
        self.scores: dict[str, ScoreDesc] = {}
        for annotator_info in score_annotators:
            assert len(annotator_info.resources) == 1, annotator_info
            resource = annotator_info.resources[0]
            if resource.get_type() not in {
                    "position_score", "np_score", "allele_score"}:
                logger.warning(
                    "wrong resource type passed to genomic scores: %s",
                    resource.resource_id)
                continue
            scores_descriptions = \
                self._build_annotator_scores_desc(annotator_info)
            self.scores.update(scores_descriptions)
        logger.info(
            "genomic scores histograms loaded: %s", list(self.scores.keys()))

    @staticmethod
    def _build_annotator_scores_desc(
            annotator_info: AnnotatorInfo) -> dict[str, ScoreDesc]:
        resource = annotator_info.resources[0]
        score = build_score_from_resource(resource)
        result = {}
        for attr in annotator_info.attributes:
            if attr.internal:
                continue
            score_def = score.score_definitions[attr.source]
            score_desc = ScoreDesc(
                resource.resource_id,
                attr.source, attr.source,
                attr.name,
                score.get_score_histogram(attr.source),
                score_def.desc,
                resource.get_description()
            )
            if score_desc.hist is None:
                logger.warning(
                    "unable to load histogram for %s: %s (%s)",
                    score.resource_id, attr.name, attr.source)
                continue
            result[attr.name] = score_desc
        return result

    def get_scores(self) -> list[tuple[str, ScoreDesc]]:
        """Return all genomic scores histograms."""
        result = []

        for score_id, score in self.scores.items():
            result.append((score_id, score))

        return result

    def __getitem__(self, score_id: str) -> ScoreDesc:
        if score_id not in self.scores:
            raise KeyError()

        res = self.scores[score_id]
        return res

    def __contains__(self, score_id: str) -> bool:
        return score_id in self.scores

    def __len__(self) -> int:
        return len(self.scores)
