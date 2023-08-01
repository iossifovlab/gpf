import logging
from dataclasses import dataclass
from typing import Optional, Union

from dae.genomic_resources.genomic_scores import build_score_from_resource
from dae.genomic_resources.histogram import NumberHistogram, \
    CategoricalHistogram, NullHistogram


logger = logging.getLogger(__name__)


@dataclass
class ScoreDesc:
    """Data class to describe genomic scores in GenomicScoresDb."""

    resource_id: str
    score_id: str
    source: str
    destination: str
    hist: Optional[Union[NumberHistogram, CategoricalHistogram, NullHistogram]]
    description: str
    help: str


class GenomicScoresDb:
    """Genomic scores DB allowing access to genomic scores histograms."""

    def __init__(self, grr, score_annotators):
        self.grr = grr
        self.scores = {}
        for annotator_info in score_annotators:
            assert len(annotator_info.resources) == 1, annotator_info
            resource = annotator_info.resources[0]
            if resource.get_type() not in {
                    "position_score", "np_score", "allele_score"}:
                logger.warning(
                    "wrong resource type passed to genomic scores: %s",
                    resource.resource_id)
                continue
            scores_desc = self._build_annotator_scores_desc(annotator_info)
            self.scores.update(scores_desc)
        logger.info(
            "genomic scores histograms loaded: %s", list(self.scores.keys()))

    @staticmethod
    def _build_annotator_scores_desc(annotator_info):
        resource = annotator_info.resources[0]
        score = build_score_from_resource(resource)
        result = {}
        for attr in annotator_info.attributes:
            if attr.internal:
                continue
            score_desc = ScoreDesc(
                resource.resource_id,
                attr.source, attr.source,
                attr.name,
                score.get_number_histogram(attr.source),
                score.get_score_definition(attr.source).desc,
                score.resource.get_description())
            if score_desc.hist is None:
                logger.warning(
                    "unable to load histogram for %s: %s (%s)",
                    score.resource_id, attr.name, attr.source)
                continue
            result[attr.name] = score_desc
        return result

    def get_scores(self):
        """Return all genomic scores histograms."""
        result = []

        for score_id, score in self.scores.items():
            result.append((score_id, score))

        return result

    def __getitem__(self, score_id):
        if score_id not in self.scores:
            raise KeyError()

        res = self.scores[score_id]
        return res

    def __contains__(self, score_id):
        return score_id in self.scores

    def __len__(self):
        return len(self.scores)
