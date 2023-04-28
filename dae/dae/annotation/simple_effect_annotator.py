import logging
import copy
from typing import Optional, cast, Tuple, Set
from dae.annotation.annotatable import Annotatable

from dae.annotation.annotator_base import ATTRIBUTES_SCHEMA, Annotator
from dae.genomic_resources.gene_models import GeneModels, \
    build_gene_models_from_resource

from dae.genomic_resources.genomic_context import get_genomic_context

logger = logging.getLogger(__name__)


def build_simple_effect_annotator(pipeline, config):
    """Build a simple effect annotator based on pipeline and configuration."""
    config = SimpleEffectAnnotator.validate_config(config)

    if config.get("annotator_type") != SimpleEffectAnnotator.ANNOTATOR_TYPE:
        logger.error(
            "wrong usage of build_simple_effect_annotator with an "
            "annotator config: %s", config)
        raise ValueError(f"wrong annotator type: {config}")

    if config.get("gene_models") is None:
        gene_models = get_genomic_context().get_gene_models()
        if gene_models is None:
            raise ValueError(
                "can't create effect annotator: "
                "gene models are missing in config and context")
    else:
        gene_models_id = config.get("gene_models")
        resource = pipeline.repository.get_resource(gene_models_id)
        gene_models = build_gene_models_from_resource(resource).load()

    return SimpleEffectAnnotator(config, gene_models)


class SimpleEffectAnnotator(Annotator):
    """Defines simple variant effect annotator."""

    ANNOTATOR_TYPE = "simple_effect_annotator"

    DEFAULT_ANNOTATION = {
        "attributes": [
            {"source": "effect"},
            {"source": "genes"},
        ]
    }

    @classmethod
    def validate_config(cls, config: dict) -> dict:
        schema = {
            "annotator_type": {
                "type": "string",
                "required": True,
                "allowed": [SimpleEffectAnnotator.ANNOTATOR_TYPE]
            },
            "gene_models": {
                "type": "string",
                "nullable": True,
                "default": None,
            },
            "attributes": {
                "type": "list",
                "nullable": True,
                "default": None,
                "schema": ATTRIBUTES_SCHEMA
            }
        }

        validator = cls.ConfigValidator(schema)
        validator.allow_unknown = True

        logger.debug("validating effect annotator config: %s", config)
        if not validator.validate(config):
            logger.error(
                "wrong config format for effect annotator: %s",
                validator.errors)
            raise ValueError(
                f"wrong effect annotator config {validator.errors}")
        return cast(dict, validator.document)

    def __init__(
            self, config, gene_models: GeneModels):
        super().__init__(config)

        assert isinstance(gene_models, GeneModels)

        self.gene_models = gene_models

        self._annotation_schema = None
        self._annotation_config: Optional[list[dict[str, str]]] = None

        self._open = False

    def get_all_annotation_attributes(self) -> list[dict]:
        result = [
            {
                "name": "effect",
                "type": "str",
                "desc": "The worst effect.",
            },
            {
                "name": "genes",
                "type": "str",
                "desc": "Genes."
            },
            {
                "name": "gene_list",
                "type": "object",
                "desc": "List of all genes"
            },
        ]
        return result

    def _not_found(self, attributes):
        for attr in self.get_annotation_config():
            attributes[attr["destination"]] = ""

    # TODO

    def run_annotate(self, chrom: str, beg: int, end: int) \
            -> Tuple[str, Set[str]]:
        # self.gene_models should be used instead of gmDB
        # from dae.utils.regions import Region  instead of RO.Region

        return "gosho", set(["pesho"])

    def _do_annotate(
        self, annotatable: Annotatable, context: dict
    ) -> dict:
        result: dict = {}

        if annotatable is None:
            self._not_found(result)
            return result

        effects, gene_list = self.run_annotate(
            annotatable.chrom,
            annotatable.position,
            annotatable.end_position)
        genes = ",".join(gene_list)

        result = {
            "effect": effect,
            "genes": genes,
            "gene_list": gene_list
        }

        return result

    def annotator_type(self) -> str:
        return SimpleEffectAnnotator.ANNOTATOR_TYPE

    def get_annotation_config(self) -> list[dict]:
        if self._annotation_config is None:
            if self.config.get("attributes"):
                self._annotation_config = copy.deepcopy(
                    self.config.get("attributes"))
            else:
                self._annotation_config = copy.deepcopy(
                    self.DEFAULT_ANNOTATION["attributes"])
        return self._annotation_config

    def close(self):
        self._open = False
        pass

    def open(self):
        self._open = True
        self.gene_models.load()
        return self

    def is_open(self):
        return self._open

    @property
    def resources(self) -> set[str]:
        return {
            self.gene_models.resource_id
        }
