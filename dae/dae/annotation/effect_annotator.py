import logging
import textwrap
from typing import Any

from dae.annotation.annotatable import Annotatable, CNVAllele, VCFAllele
from dae.annotation.annotation_config import (
    AnnotationConfigParser,
    AnnotatorInfo,
)
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
    Annotator,
)
from dae.annotation.annotator_base import AnnotatorBase
from dae.effect_annotation.annotator import EffectAnnotator
from dae.effect_annotation.effect import (
    AlleleEffects,
    AnnotationEffect,
    EffectTypesMixin,
)
from dae.genomic_resources.gene_models import (
    GeneModels,
    build_gene_models_from_resource,
)
from dae.genomic_resources.genomic_context import get_genomic_context
from dae.genomic_resources.reference_genome import (
    ReferenceGenome,
    build_reference_genome_from_resource_id,
)

logger = logging.getLogger(__name__)


def build_effect_annotator(pipeline: AnnotationPipeline,
                           info: AnnotatorInfo) -> Annotator:
    return EffectAnnotatorAdapter(pipeline, info)


class EffectAnnotatorAdapter(AnnotatorBase):
    """Adapts effect annotator to be used in annotation infrastructure."""

    def __init__(self, pipeline: AnnotationPipeline, info: AnnotatorInfo):
        gene_models_resource_id = info.parameters.get("gene_models")
        if gene_models_resource_id is None:
            gene_models = get_genomic_context().get_gene_models()
            if gene_models is None:
                raise ValueError(f"Can't create {info.type}: "
                                 "gene model resource are missing in config "
                                 "and context")
        else:
            resource = pipeline.repository.get_resource(
                gene_models_resource_id)
            gene_models = build_gene_models_from_resource(resource)
        assert isinstance(gene_models, GeneModels)

        genome_resource_id = info.parameters.get("genome") or \
            gene_models.reference_genome_id or \
            (pipeline.preamble.input_reference_genome
             if pipeline.preamble is not None else None)
        if genome_resource_id is None:
            genome = get_genomic_context().get_reference_genome()
            if genome is None:
                raise ValueError(
                    f"The {info} has no reference genome"
                    " specified and no genome was found"
                    " in the gene models' configuration,"
                    " the context or the annotation config's"
                    " preamble.")
        else:
            genome = build_reference_genome_from_resource_id(
                genome_resource_id, pipeline.repository)
        assert isinstance(genome, ReferenceGenome)


        info.documentation += textwrap.dedent("""

Annotator to identify the effect of the variant on protein coding.

<a href="https://iossifovlab.com/gpfuserdocs/administration/annotation.html#effect-annotator" target="_blank">More info</a>

""")  # noqa
        info.resources += [genome.resource, gene_models.resource]
        if not info.attributes:
            info.attributes = AnnotationConfigParser.parse_raw_attributes([
                "worst_effect",
                "effect_details",
                "gene_effects",
                {"name": "gene_list", "internal": True},
            ])

        self.effect_types_gene_lists = {}
        for group in EffectTypesMixin.EFFECT_GROUPS:
            self.effect_types_gene_lists[f"{group}_gene_list"] = (
                "object",
                f"List of all {group} genes",
            )
        for effect_type in EffectTypesMixin.EFFECT_TYPES:
            self.effect_types_gene_lists[f"{effect_type}_gene_list"] = (
                "object",
                f"List of all {effect_type} genes",
            )
        self.effect_types_gene_lists["LGD_gene_list"] = (
            "object",
            "List of all LGD genes (deprecated, use LGDs_gene_list)",
        )
        super().__init__(pipeline, info, {
            "worst_effect": ("str", "Worst effect accross all transcripts."),
            "gene_effects": ("str", "Effects types for genes. Format: "
                                    "`<gene_1>:<effect_1>|...` A gene can "
                                    "be repeated."),
            "effect_details": ("str", "Effect details for each affected "
                                      "transcript. Format: `< transcript 1 >:"
                                      "<gene 1>:<effect 1>:<details 1>|...`"),
            "allele_effects": ("object", "The a list of a python objects with "
                                         "details of the effects for each "
                                         "affected transcript."),
            "gene_list": ("object", "List of all genes"),
            **self.effect_types_gene_lists,
        })

        self.used_attributes = [
            attr.source for attr in self.get_info().attributes
        ]
        self.genome = genome
        self.gene_models = gene_models
        self._promoter_len = info.parameters.get("promoter_len", 0)
        self._region_length_cutoff = info.parameters.get(
            "region_length_cutoff", 15_000_000)
        self.effect_annotator = EffectAnnotator(
            self.genome,
            self.gene_models,
            promoter_len=self._promoter_len,
        )

    def close(self) -> None:
        self.genome.close()
        self.gene_models.close()
        assert self.effect_annotator is not None
        self.effect_annotator.close()
        self.effect_annotator = None  # type: ignore
        super().close()

    def open(self) -> Annotator:
        self.genome.open()
        self.gene_models.load()
        return super().open()

    def _not_found(self, attributes: dict[str, Any]) -> dict[str, Any]:
        effect_type = "unknown"
        effect = AnnotationEffect(effect_type)
        full_desc = AnnotationEffect.effects_description([effect])
        attributes.update({
            "worst_effect": full_desc[0],
            "gene_effects": full_desc[1],
            "effect_details": full_desc[2],
            "allele_effects": AlleleEffects.from_effects([effect]),
            "gene_list": [],
            "lgd_gene_list": [],
        })
        return attributes

    def _region_length_cutoff_effect(
        self, attributes: dict[str, Any], annotatable: Annotatable,
    ) -> dict[str, Any]:
        if annotatable.type == Annotatable.Type.LARGE_DELETION:
            effect_type = "CNV-"
        elif annotatable.type == Annotatable.Type.LARGE_DUPLICATION:
            effect_type = "CNV+"
        else:
            effect_type = "unknown"
        effect = AnnotationEffect(effect_type)
        effect.length = len(annotatable)
        full_desc = AnnotationEffect.effects_description([effect])
        attributes.update({
            "worst_effect": full_desc[0],
            "gene_effects": full_desc[1],
            "effect_details": full_desc[2],
            "allele_effects": AlleleEffects.from_effects([effect]),
            "gene_list": [],
            "lgd_gene_list": [],
        })
        return attributes

    def _do_annotate(
        self, annotatable: Annotatable,
        context: dict[str, Any],  # noqa: ARG002
    ) -> dict[str, Any]:
        result: dict = {}
        if annotatable is None:
            return self._not_found(result)

        length = len(annotatable)
        if isinstance(annotatable, VCFAllele):
            try:
                assert self.effect_annotator is not None
                effects = self.effect_annotator.annotate_allele(
                    chrom=annotatable.chromosome,
                    pos=annotatable.position,
                    ref=annotatable.reference,
                    alt=annotatable.alternative,
                    variant_type=annotatable.type.name,
                    length=length,
                )
            except Exception:  # pylint: disable=broad-except
                logger.exception(
                    "unable to create effect annotation for allele %s",
                    annotatable)
                return self._not_found(result)

        elif length > self._region_length_cutoff:
            logger.warning(
                "region length %s is longer than cutoff %s; %s",
                length, self._region_length_cutoff, annotatable)
            return self._region_length_cutoff_effect(result, annotatable)
        elif isinstance(annotatable, CNVAllele):
            assert self.effect_annotator is not None
            effects = self.effect_annotator.annotate_cnv(
                annotatable.chrom,
                annotatable.pos, annotatable.pos_end, annotatable.type)
        elif isinstance(annotatable, Annotatable):
            assert self.effect_annotator is not None

            effects = self.effect_annotator.annotate_region(
                annotatable.chrom,
                annotatable.pos, annotatable.pos_end)
        else:
            raise ValueError(f"unexpected annotatable: {type(annotatable)}")

        gene_list = list(set(
            AnnotationEffect.gene_effects(effects)[0],
        ))

        full_desc = AnnotationEffect.effects_description(effects)
        result = {
            "worst_effect": full_desc[0],
            "gene_effects": full_desc[1],
            "effect_details": full_desc[2],
            "allele_effects": AlleleEffects.from_effects(effects),
            "gene_list": gene_list,
        }
        for effect_gene_list in self.effect_types_gene_lists:
            if effect_gene_list in self.used_attributes:
                effect_type = effect_gene_list.split("_")[0]
                if effect_type == "LGD":
                    effect_type = "LGDs"
                result[effect_gene_list] = \
                    AnnotationEffect.filter_gene_effects(
                        effects, effect_type)[0]

        return result
