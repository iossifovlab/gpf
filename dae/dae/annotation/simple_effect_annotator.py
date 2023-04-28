import logging
import copy
from typing import Optional, cast, Tuple, Set
from dae.annotation.annotatable import Annotatable

from dae.annotation.annotator_base import ATTRIBUTES_SCHEMA, Annotator
from dae.genomic_resources.gene_models import GeneModels, \
    build_gene_models_from_resource

from dae.genomic_resources.genomic_context import get_genomic_context
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
    def CDS_intron_regions(self, tm):
        r = []
        if not tm.is_coding(): return r
        for ei in range(len(tm.exons)-1):
            bg = tm.exons[ei].stop + 1
            en = tm.exons[ei+1].start + 1
            if bg > tm.cds[0] and en < tm.cds[1]:
                r.append(Region(tm.chrom, bg, en))
        return r

    def UTR_regions(self, tm):
        r = []
        if not tm.is_coding(): return r
        utr5_regions=tm.UTR5_regions()
        utr3_regions=tm.UTR3_regions()
        utr3_regions.extend(utr3_regions)
        return utr5_regions

    def peripheral_regions(self, tm):
        r = []
        if not tm.is_coding(): return r
        
        if tm.cds[0] > tm.tx[0]:
            r.append(Region(tm.chrom, tm.tx[0], tm.cds[0] - 1))
        if tm.cds[1] < tm.tx[1]:
            r.append(Region(tm.chrom, tm.cds[1] + 1, tm.tx[1]))
        return r 

    def noncoding_regions(self, tm):
        r = []
        if tm.is_coding(): return r
        r.append(Region(tm.chrom, tm.tx[0], tm.tx[1]))
        return r

    def run_annotate(self, chrom: str, beg: int, end: int) \
            -> Tuple[str, Set[str]]:
        
         # self.gene_models should be used instead of gmDB
        # from dae.utils.regions import Region  instead of RO.Region
        # print(self.gene_models.gene_names())
        effect_region = Region(chrom, beg, end)
        for (start, stop), tms in self.gene_models.utr_models[chrom].items():
            # if effect_region.intersection(Region(chrom, start, stop)):
            if (beg <= stop and end >= start):
                
                ## test for coding 
                genes = set()
                for tm in tms:
                    if tm.gene in genes: continue
                    for r in tm.CDS_regions():
                        assert r.chrom == chrom

                        if r.stop >= beg and r.start <= end:
                            genes.add(tm.gene)
                            break
                if genes: 
                    return 'coding', genes
                    
                ## test for UTR 
                genes = set()
                for tm in tms:
                    if tm.gene in genes: continue
                    for r in self.UTR_regions(tm):
                        assert r.chrom == chrom
                        
                        if r.stop >= beg and r.start <= end:
                            genes.add(tm.gene)
                            break
                if genes: 
                    return 'peripheral', genes
                
                ## test for intercoding_intronic 
                genes = set()
                for tm in tms:
                    for tm.gene in genes: continue
                    for r in self.CDS_intron_regions(tm):
                        assert r.chrom == chrom
                        if r.start <= beg and end <= r.stop:
                            genes.add(tm.gene)
                            break
                if genes:
                    return 'inter-coding_intronic', genes
                
                ## test for peripheral
                genes = set()
                for tm in tms:
                    for tm.gene in genes: continue
                    for r in self.peripheral_regions(tm):
                        assert r.chrom == chrom
                        if r.stop >= beg and r.start <= end:
                            genes.add(tm.gene)
                            break
                if genes:
                    return 'peripheral', genes
                
                ## test for noncoding 
                genes = set()
                for tm in tms:
                    if tm.gene in genes: continue
                    for r in self.noncoding_regions(tm):
                        assert r.chrom == chrom
                        if r.stop >= beg and r.start <= end:
                            genes.add(tm.gene)
                            break
                if genes:
                    return 'noncoding', genes
        
        return 'intergenic', []
        # return "gosho", set(["pesho"])

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
