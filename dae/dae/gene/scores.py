from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Any, Optional

from jinja2 import Template

from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.genomic_scores import build_score_from_resource, \
    GenomicScore
from dae.genomic_resources.histogram import NumberHistogram, \
    CategoricalHistogram, NullHistogram, Histogram
from dae.annotation.annotation_pipeline import AnnotatorInfo, AttributeInfo


logger = logging.getLogger(__name__)


@dataclass
class ScoreDesc:
    """Data class to describe genomic scores in GenomicScoresDb."""

    name: str
    resource_id: str
    source: str
    hist: Histogram
    description: str
    help: str
    small_values_desc: Optional[str]
    large_values_desc: Optional[str]

    def to_json(self) -> dict[str, Any]:
        hist_data = self.hist.to_dict()
        return {
            "name": self.name,
            "resource_id": self.resource_id,
            "source": self.source,
            "hist": hist_data,
            "description": self.description,
            "help": self.help,
            "small_values_desc": self.small_values_desc,
            "large_values_desc": self.large_values_desc
        }

    @staticmethod
    def from_json(data: dict[str, Any]) -> ScoreDesc:
        """Build a ScoreDesc from a JSON."""
        assert "hist" in data
        hist_type = data["hist"]["config"]["type"]
        if hist_type == "categorical":
            hist_data: Histogram = CategoricalHistogram.from_dict(data["hist"])
        elif hist_type == "null":
            hist_data = NullHistogram.from_dict(data["hist"])
        elif hist_type == "number":
            hist_data = NumberHistogram.from_dict(data["hist"])
        else:
            raise ValueError(f"Unknown histogram type {hist_type}")
        return ScoreDesc(
            data["name"],
            data["resource_id"],
            data["source"],
            hist_data,
            data["description"],
            data["help"],
            data.get("small_values_desc"),
            data.get("large_values_desc")
        )


SCORE_ATTRIBUTE_DESCRIPTION = """

<div class="score-description">

## {{ data.name }}

{{ data.description}}

{{ data.resource_summary }}

{{ data.histogram }}

Genomic resource: <a href={{data.resource_url}} target="_blank">{{ data.resource_id }}</a>

<details>

<summary class="details">

#### Details

</summary>

<div class="details-body">

##### Attribute properties:

* **source**: {{ data.source }}

</div>

</details>

</div>

"""

SCORE_ATTRIBUTE_HISTOGRAM = """
<div class="modal-histogram">

<div class="histogram-image">

![HISTOGRAM]({{ hist_url }})

</div>

{%- if score_def.small_values_desc and score_def.large_values_desc %}

<div class="values-desc">

<span class="small-values">

{{ score_def.small_values_desc}}

</span>

<span class="large-values">

{{ score_def.large_values_desc}}

</span>

</div>

{%- endif %}

</div>
"""


def _build_score_description(
    attr_info: AttributeInfo,
    genomic_score: GenomicScore,
    # annotator_info: AnnotatorInfo
) -> str:
    hist_url = genomic_score.get_histogram_image_url(attr_info.source)
    score_def = genomic_score.get_score_definition(attr_info.source)
    assert score_def is not None

    histogram = Template(SCORE_ATTRIBUTE_HISTOGRAM).render(
        hist_url=hist_url,
        score_def=score_def
    )

    data = {
        "name": attr_info.name,
        "description": attr_info.description,
        "resource_id": genomic_score.resource_id,
        "resource_summary": genomic_score.resource.get_summary(),
        "resource_url": f"{genomic_score.resource.get_url()}/index.html",
        "histogram": histogram,
        "source": attr_info.source,
    }
    template = Template(SCORE_ATTRIBUTE_DESCRIPTION)
    return template.render(data=data)


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
        annotator_info: AnnotatorInfo
    ) -> dict[str, ScoreDesc]:
        resource = annotator_info.resources[0]
        score = build_score_from_resource(resource)
        result = {}
        for attr in annotator_info.attributes:
            if attr.internal:
                continue
            score_def = score.score_definitions[attr.source]
            description = _build_score_description(attr, score)
            score_desc = ScoreDesc(
                attr.name,
                resource.resource_id,
                attr.source,
                score.get_score_histogram(attr.source),
                f"{attr.name} - {attr.description}",
                description,
                score_def.small_values_desc,
                score_def.large_values_desc
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
