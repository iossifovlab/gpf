import logging
import copy
from typing import Optional, cast, Tuple, Set
from dae.annotation.annotatable import Annotatable

from dae.annotation.annotator_base import ATTRIBUTES_SCHEMA, AnnotatorBase, AnnotatorConfigValidator
from dae.genomic_resources.gene_models import GeneModels, \
    build_gene_models_from_resource

from dae.genomic_resources.genomic_context import get_genomic_context
from dae.genomic_resources.repository import GenomicResource
from dae.utils.regions import Region

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


class SimpleEffectAnnotator(AnnotatorBase):
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

        validator = AnnotatorConfigValidator(schema)
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

    def cds_intron_regions(self, transcript):
        """Return whether region is CDS intron."""
        region: list[Region] = []
        if not transcript.is_coding():
            return region
        for index in range(len(transcript.exons) - 1):
            beg = transcript.exons[index].stop + 1
            end = transcript.exons[index + 1].start + 1
            if beg > transcript.cds[0] and end < transcript.cds[1]:
                region.append(Region(transcript.chrom, beg, end))
        return region

    def utr_regions(self, transcript):
        """Return whether the region is classified as UTR."""
        region: list[Region] = []
        if not transcript.is_coding():
            return region

        utr5_regions = transcript.UTR5_regions()
        utr3_regions = transcript.UTR3_regions()
        utr3_regions.extend(utr3_regions)
        return utr5_regions

    def peripheral_regions(self, transcript):
        """Return whether the region is peripheral."""
        region: list[Region] = []
        if not transcript.is_coding():
            return region

        if transcript.cds[0] > transcript.tx[0]:
            region.append(
                Region(transcript.chrom, transcript.tx[0],
                       transcript.cds[0] - 1))

        if transcript.cds[1] < transcript.tx[1]:
            region.append(
                Region(transcript.chrom, transcript.cds[1] + 1,
                       transcript.tx[1]))

        return region

    def noncoding_regions(self, transcript):
        """Return whether the region is noncoding."""
        region: list[Region] = []
        if transcript.is_coding():
            return region

        region.append(
            Region(transcript.chrom, transcript.tx[0],
                   transcript.tx[1]))
        return region

    def call_region(
        self, chrom, beg, end, transcripts, func_name, classification
    ) -> Optional[Tuple[str, Set[str]]]:
        """Call a region with a specific classification."""
        genes = set()
        for transcript in transcripts:
            if transcript.gene in genes:
                continue

            regions = []
            if func_name == "CDS_regions":
                regions = transcript.CDS_regions()
            else:
                regions = getattr(self, func_name)(transcript)

            for region in regions:
                assert region.chrom == chrom
                if region.stop >= beg and region.start <= end:
                    genes.add(transcript.gene)
                    break
        if genes:
            return classification, genes
        return None

    def run_annotate(
        self, chrom: str, beg: int, end: int
    ) -> Tuple[str, Set[str]]:
        """Return classification with a set of affected genes."""
        assert self.gene_models.utr_models is not None
        assert self.gene_models.utr_models[chrom] is not None

        for (start, stop), tms in self.gene_models.utr_models[chrom].items():
            if (beg <= stop and end >= start):

                result = self.call_region(
                    chrom, beg, end, tms, "CDS_regions", "coding")

                if not result:
                    result = self.call_region(
                        chrom, beg, end, tms, "utr_regions", "peripheral")
                else:
                    return result

                if not result:
                    result = self.call_region(
                        chrom, beg, end, tms, "cds_intron_regions",
                        "inter-coding_intronic")
                else:
                    return result

                if not result:
                    result = self.call_region(
                        chrom, beg, end, tms, "peripheral_regions",
                        "peripheral")
                else:
                    return result

                if not result:
                    result = self.call_region(
                        chrom, beg, end, tms, "noncoding_regions", "noncoding")
                else:
                    return result

        return "intergenic", set()

    def _do_annotate(
        self, annotatable: Annotatable, context: dict
    ) -> dict:
        result: dict = {}

        if annotatable is None:
            self._not_found(result)
            return result

        effect, gene_list = self.run_annotate(
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

    def get_annotation_config(self):
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

    def open(self):
        self._open = True
        self.gene_models.load()
        return self

    def is_open(self):
        return self._open

    @property
    def resources(self) -> list[GenomicResource]:
        return [self.gene_models.resource]
