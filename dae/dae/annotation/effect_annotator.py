import logging
import textwrap
from typing import Any

from dae.annotation.annotatable import Annotatable, CNVAllele, VCFAllele
from dae.annotation.annotation_config import (
    AnnotatorInfo,
)
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
    Annotator,
)
from dae.annotation.annotator_base import (
    AnnotatorBase,
    AttributeDesc,
)
from dae.annotation.utils import (
    find_annotator_gene_models,
    find_annotator_reference_genome,
)
from dae.effect_annotation.annotator import EffectAnnotator
from dae.effect_annotation.effect import (
    AlleleEffects,
    AnnotationEffect,
    EffectTypesMixin,
)
from dae.genomic_resources.aggregators import (
    Aggregator,
    build_aggregator,
    validate_aggregator,
)

logger = logging.getLogger(__name__)


def build_effect_annotator(pipeline: AnnotationPipeline,
                           info: AnnotatorInfo) -> Annotator:
    return EffectAnnotatorAdapter(pipeline, info)


class EffectAnnotatorAdapter(AnnotatorBase):
    """Adapts effect annotator to be used in annotation infrastructure."""

    def __init__(self, pipeline: AnnotationPipeline, info: AnnotatorInfo):
        gene_models = find_annotator_gene_models(
            info, pipeline.repository)
        genome = find_annotator_reference_genome(
            info, gene_models, pipeline, pipeline.repository)

        info.documentation += textwrap.dedent("""

Annotator to identify the effect of the variant on protein coding.

<a href="https://iossifovlab.com/gpfuserdocs/administration/annotation.html#effect-annotator" target="_blank">More info</a>

""")  # noqa
        info.resources += [genome.resource, gene_models.resource]
        super().__init__(pipeline, info)

        self.used_attributes = [
            attr.source for attr in self.get_info().attributes
        ]
        self.genome = genome
        self.gene_models = gene_models
        self._promoter_len = info.parameters.get("promoter_len", 0)
        self._region_length_cutoff = info.parameters.get(
            "region_length_cutoff", 15_000_000)

        self.gene_list_aggregators: dict[str, Aggregator] = {}
        for attr in info.attributes:
            gene_list_aggregator = attr.parameters.get("gene_list_aggregator")
            if gene_list_aggregator is None:
                continue

            validate_aggregator(gene_list_aggregator)
            assert isinstance(gene_list_aggregator, str)
            attr_desc = self.attribute_descriptions[attr.source]
            if attr_desc.type != "object" \
                    or not attr_desc.params.get("gene_list"):
                raise ValueError(
                    f"Attribute {attr.source} is not a gene list attribute "
                    f"but gene_list_aggregator is specified.")
            self.gene_list_aggregators[attr.name] = build_aggregator(
                gene_list_aggregator)

        self.effect_annotator = EffectAnnotator(
            self.genome,
            self.gene_models,
            promoter_len=self._promoter_len,
        )

    def get_all_attribute_descriptions(self) -> dict[str, AttributeDesc]:
        effect_gene_lists = {}
        effect_genes = {}
        for group in [
                *EffectTypesMixin.EFFECT_GROUPS,
                *EffectTypesMixin.EFFECT_TYPES]:
            effect_gene_lists[f"{group}_gene_list"] = AttributeDesc(
                f"{group}_gene_list",
                "object",
                f"List of all {group} genes",
                internal=True,
                default=False,
                params={
                    "effect_type": group,
                    "gene_list": True,
                },
            )
            effect_genes[f"{group}_genes"] = AttributeDesc(
                f"{group}_genes",
                "str", f"Comma separated list of {group} genes",
                internal=False,
                default=False,
                params={
                    "effect_type": group,
                },
            )
        effect_gene_lists["LGD_gene_list"] = AttributeDesc(
            "LGD_gene_list",
            "object",
            "List of all LGD genes (deprecated, use LGDs_gene_list)",
            internal=True,
            default=False,
            params={
                "effect_type": "LGDs",
                "gene_list": True,
            },
        )
        return {
            "worst_effect": AttributeDesc(
                "worst_effect",
                "str", "Worst effect accross all transcripts.",
                default=True,
                internal=False),
            "worst_effect_genes": AttributeDesc(
                "worst_effect_genes",
                "str", "comma separated list of genes with worst effect.",
                internal=False,
                default=True,
                params={
                    "gene_list": True,
                }),
            "worst_effect_gene_list": AttributeDesc(
                "worst_effect_gene_list",
                "object", "list of genes with worst effect.",
                internal=True,
                default=False),
            "gene_effects": AttributeDesc(
                "gene_effects",
                "str", "`<gene_1>:<effect_1>|...` A gene can be repeated.",
                internal=False,
                default=True),
            "effect_details": AttributeDesc(
                "effect_details",
                "str", "Effect details for each affected "
                "transcript. Format: `< transcript 1 >:"
                "<gene 1>:<effect 1>:<details 1>|...`",
                internal=False,
                default=True),
            "allele_effects": AttributeDesc(
                "allele_effects",
                "object", "The a list of a python objects with "
                "details of the effects for each "
                "affected transcript.",
                internal=True,
                default=False),
            "gene_list": AttributeDesc(
                "gene_list",
                "object", "List of all genes",
                internal=True,
                default=True,
                params={
                    "gene_list": True,
                }),
            "genes": AttributeDesc(
                "genes",
                "str", "Comma separated list of all affected genes.",
                internal=False,
                default=False),
            **effect_gene_lists,
            **effect_genes,
        }

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
            "genes": "",
            "worst_effect_gene_list": [],
            "worst_effect_genes": "",
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
            "genes": "",
            "worst_effect_gene_list": [],
            "worst_effect_genes": "",
        })
        return attributes

    def _do_annotate(
        self, annotatable: Annotatable,
        context: dict[str, Any],  # noqa: ARG002
    ) -> dict[str, Any]:
        result: dict = {}

        length = len(annotatable)
        if isinstance(annotatable, VCFAllele):
            try:
                assert self.effect_annotator is not None

                effects = self.effect_annotator.annotate_allele(
                    chrom=annotatable.chromosome,
                    pos=annotatable.position,
                    ref=annotatable.reference,
                    alt=annotatable.alternative,
                    variant_type=annotatable.type,
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

        gene_list = AnnotationEffect.genes(effects)

        full_desc = AnnotationEffect.effects_description(effects)
        worst_effect = full_desc[0]
        worst_effect_genes = AnnotationEffect.filter_genes(
            effects, worst_effect)
        result = {
            "worst_effect": full_desc[0],
            "gene_effects": full_desc[1],
            "effect_details": full_desc[2],
            "allele_effects": AlleleEffects.from_effects(effects),
            "gene_list": gene_list,
            "genes": ",".join(gene_list),
            "worst_effect_gene_list": worst_effect_genes,
            "worst_effect_genes": ",".join(worst_effect_genes),
        }
        for attr in self.attributes:
            attr_desc = self.attribute_descriptions[attr.source]
            effect_type = attr_desc.params.get("effect_type")
            if effect_type is not None:
                genes = sorted(
                    AnnotationEffect.filter_genes(effects, effect_type))
                if attr_desc.params.get("gene_list"):
                    result[attr.source] = genes
                else:
                    result[attr.source] = ",".join(genes)
        return result

    def annotate(
        self, annotatable: Annotatable | None, context: dict[str, Any],
    ) -> dict[str, Any]:
        if annotatable is None:
            return self._empty_result()
        source_values = self._do_annotate(annotatable, context)
        result: dict[str, Any] = {}
        for attr in self.get_info().attributes:
            if attr.name not in self.gene_list_aggregators:
                result[attr.name] = source_values[attr.source]
                continue
            aggregator = self.gene_list_aggregators[attr.name]
            result[attr.name] = aggregator.aggregate(
                source_values[attr.source])

        return result
