import logging
import copy

from typing import List, Dict, cast
from .annotatable import Annotatable
from dae.gene.gene_scores import GeneScore
from .annotator_base import Annotator, ATTRIBUTES_SCHEMA
from dae.genomic_resources.aggregators import AGGREGATOR_SCHEMA

logger = logging.getLogger(__name__)


class GeneScoreAnnotator(Annotator):
    def __init__(
            self, config: dict,
            resource):
        super().__init__(config)

        self.resource = resource
        resource_scores = GeneScore.load_gene_scores_from_resource(
            resource
        )
        resource_scores = {gs.score_id: gs for gs in resource_scores}
        self.gene_scores = resource_scores

        self._annotation_schema = None

    def annotator_type(self) -> str:
        return "gene_score_annotator"

    def get_all_annotation_attributes(self) -> List[Dict]:
        result = []
        for gs in self.gene_scores.values():
            result.append({
                "name": gs.id,
                "type": "object",
                "desc": gs.desc
            })
        return result

    def get_annotation_config(self) -> List[Dict]:
        attributes: List[dict] = self.config.get("attributes", [])

        return attributes

    @classmethod
    def validate_config(cls, config: Dict) -> Dict:
        schema = {
            "annotator_type": {
                "type": "string",
                "required": True,
                "allowed": ["gene_score_annotator"]
            },
            "input_annotatable": {
                "type": "string",
                "nullable": True,
                "default": None,
            },
            "resource_id": {"type": "string"},
            "input_gene_list": {"type": "string"},
            "attributes": {
                "type": "list",
                "schema": None
            }
        }

        attr_schema = copy.deepcopy(ATTRIBUTES_SCHEMA)
        schema["attributes"]["schema"] = attr_schema

        attributes_schema = schema["attributes"]["schema"]["schema"]
        aggr_schema = copy.deepcopy(AGGREGATOR_SCHEMA)
        attributes_schema["gene_aggregator"] = aggr_schema

        validator = cls.ConfigValidator(schema)
        validator.allow_unknown = True

        logger.debug(f"validating gene score annotator config: {config}")
        if not validator.validate(config):
            logger.error(
                f"wrong config format for gene score annotator: "
                f"{validator.errors}")
            raise ValueError(
                f"wrong gene score annotator config {validator.errors}")
        return cast(Dict, validator.document)

    def _do_annotate(self, annotatable: Annotatable, _context: Dict):
        attributes: dict = {}

        input_gene_list = self.config["input_gene_list"]
        genes = _context.get(input_gene_list)
        assert genes is not None
        for attr in self.config["attributes"]:
            src = attr["source"]
            aggregator_type = attr.get("gene_aggregator")
            gene_score = self.gene_scores[src]

            attributes[src] = gene_score.aggregate_gene_values(
                genes, aggregator_type
            )

        return attributes
