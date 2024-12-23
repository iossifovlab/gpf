"""Base classes and helpers for variant loaders."""
from __future__ import annotations

import logging
import os
import pathlib
from typing import (
    ClassVar,
)

from dae.annotation.annotation_pipeline import AnnotationPipeline, AttributeInfo
from dae.effect_annotation.effect import AlleleEffects
from dae.variants_loaders.raw.loader import (
    FullVariantsIterator,
    VariantsLoader,
    VariantsLoaderDecorator,
)

logger = logging.getLogger(__name__)

SEP1 = "!"
SEP2 = "|"
SEP3 = ":"

CLEAN_UP_COLUMNS: set[str] = {
    "alternatives_data",
    "family_variant_index",
    "family_id",
    "variant_sexes",
    "variant_roles",
    "variant_inheritance",
    "variant_in_member",
    "genotype_data",
    "best_state_data",
    "genetic_model_data",
    "inheritance_data",
    "frequency_data",
    "genomic_scores_data",
    "effect_type",
    "effect_gene",
}


def build_annotation_filename(filename: str) -> str:
    """Return the corresponding annotation file for filename."""
    path = pathlib.Path(filename)
    suffixes = path.suffixes

    if not suffixes:
        return f"{filename}-eff.txt"

    suffix = "".join(suffixes)
    replace_with = suffix.replace(".", "-")
    filename = filename.replace(suffix, replace_with)

    return f"{filename}-eff.txt"


def has_annotation_file(variants_filename: str) -> bool:
    annotation_filename = AnnotationDecorator\
        .build_annotation_filename(variants_filename)
    return os.path.exists(annotation_filename)


def save_annotation_file(
    variants_loader: AnnotationPipelineDecorator,
    filename: str, sep: str = "\t",
) -> None:
    """Save annotation file."""
    common_columns = [
        "chrom",
        "position",
        "reference",
        "alternative",
        "bucket_index",
        "summary_index",
        "allele_index",
        "allele_count",
    ]

    if variants_loader.annotation_schema is not None:
        other_columns = list(
            filter(
                lambda name: name not in common_columns
                and name not in CLEAN_UP_COLUMNS,
                [attr.name for attr in variants_loader.annotation_schema],
            ),
        )
    else:
        other_columns = []

    header = common_columns.copy()
    header.extend(["effects"])
    header.extend(other_columns)

    with open(filename, "w", encoding="utf8") as outfile:
        outfile.write(sep.join(header))
        outfile.write("\n")

        for summary_variant, _ in variants_loader.full_variants_iterator():
            for allele_index, summary_allele in enumerate(
                    summary_variant.alleles):

                line = []
                rec = summary_allele.attributes
                rec["allele_index"] = allele_index

                line_values = [
                    *[rec.get(col, "") for col in common_columns],
                    summary_allele.effects,
                    *[rec.get(col, "") for col in other_columns],
                ]

                line = [
                    str(value) if value is not None else ""
                    for value in line_values
                ]

                outfile.write(sep.join(line))
                outfile.write("\n")


class AnnotationDecorator(VariantsLoaderDecorator):
    """Base class for annotators."""

    SEP1 = "!"
    SEP2 = "|"
    SEP3 = ":"

    CLEAN_UP_COLUMNS: ClassVar[set[str]] = {
        "alternatives_data",
        "family_variant_index",
        "family_id",
        "variant_sexes",
        "variant_roles",
        "variant_inheritance",
        "variant_in_member",
        "genotype_data",
        "best_state_data",
        "genetic_model_data",
        "inheritance_data",
        "frequency_data",
        "genomic_scores_data",
        "effect_type",
        "effect_gene",
    }

    @staticmethod
    def build_annotation_filename(filename: str) -> str:
        """Return the corresponding annotation file for filename."""
        return build_annotation_filename(filename)

    @staticmethod
    def has_annotation_file(variants_filename: str) -> bool:
        return has_annotation_file(variants_filename)

    @staticmethod
    def save_annotation_file(
        variants_loader: AnnotationPipelineDecorator,
        filename: str, sep: str = "\t",
    ) -> None:
        """Save annotation file."""
        save_annotation_file(variants_loader, filename, sep)


class AnnotationPipelineDecorator(AnnotationDecorator):
    """Annotate variants by processing them through an annotation pipeline."""

    def __init__(
        self, variants_loader: VariantsLoader,
        annotation_pipeline: AnnotationPipeline,
    ) -> None:
        super().__init__(variants_loader)

        self.annotation_pipeline = annotation_pipeline
        logger.debug(
            "creating annotation pipeline decorator with "
            "annotation pipeline: %s", annotation_pipeline.get_attributes())

        self.set_attribute("annotation_schema", self.annotation_schema)
        self.set_attribute(
            "extra_attributes",
            variants_loader.get_attribute("extra_attributes"),
        )

    @property
    def annotation_schema(self) -> list[AttributeInfo]:
        return self.annotation_pipeline.get_attributes()

    def full_variants_iterator(
        self,
    ) -> FullVariantsIterator:
        with self.annotation_pipeline.open() as annotation_pipeline:
            internal_attributes = {
                attr.name for attr in self.annotation_pipeline.get_attributes()
                if attr.internal
            }

            for (summary_variant, family_variants) in \
                    self.variants_loader.full_variants_iterator():
                for sallele in summary_variant.alt_alleles:
                    attributes = annotation_pipeline.annotate(
                        sallele.get_annotatable())
                    if "allele_effects" in attributes:
                        allele_effects = attributes["allele_effects"]
                        assert isinstance(allele_effects, AlleleEffects), \
                            attributes
                        # pylint: disable=protected-access
                        sallele._effects = allele_effects  # noqa: SLF001
                        del attributes["allele_effects"]
                    public_attributes = {
                        key: value for key, value in attributes.items()
                        if key not in internal_attributes
                    }
                    sallele.update_attributes(public_attributes)
                yield summary_variant, family_variants

    def close(self) -> None:
        self.annotation_pipeline.close()
