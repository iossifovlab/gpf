from __future__ import annotations

import logging
import os
import pathlib
import time

import numpy as np
import pandas as pd

from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.effect_annotation.effect import AlleleEffects
from dae.import_tools.annotation_decorators import AnnotationDecorator
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryVariant
from dae.variants_loaders.raw.loader import (
    FullVariantsIterator,
    VariantsGenotypesLoader,
    VariantsLoader,
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
    variants_loader: VariantsLoader,
    annotation_pipeline: AnnotationPipeline,
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

    annotation_schema = annotation_pipeline.get_attributes()
    other_columns = list(
        filter(
            lambda name: name not in common_columns
            and name not in CLEAN_UP_COLUMNS,
            [attr.name for attr in annotation_schema],
        ),
    )

    header = common_columns.copy()
    header.extend(["effects"])
    header.extend(other_columns)

    internal_attributes = {
        attr.name for attr in annotation_schema
        if attr.internal
    }

    with annotation_pipeline.open() as pipeline, \
            open(filename, "w", encoding="utf8") as outfile:
        outfile.write(sep.join(header))
        outfile.write("\n")

        for summary_variant, _ in variants_loader.full_variants_iterator():
            for allele_index, summary_allele in enumerate(
                    summary_variant.alleles):
                if allele_index > 0:
                    attributes = pipeline.annotate(
                        summary_allele.get_annotatable(),
                    )

                    if "allele_effects" in attributes:
                        allele_effects = attributes["allele_effects"]
                        assert isinstance(allele_effects, AlleleEffects), \
                            attributes
                        # pylint: disable=protected-access
                        summary_allele._effects = allele_effects  # noqa: SLF001
                        del attributes["allele_effects"]

                    public_attributes = {
                        key: value for key, value in attributes.items()
                        if key not in internal_attributes
                    }
                    summary_allele.update_attributes(public_attributes)
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


def _convert_array_of_strings(token: str) -> list[str] | None:
    if not token:
        return None
    token = token.strip()
    return [w.strip() for w in token.split(SEP1)]


def _convert_string(token: str) -> str | None:
    if not token:
        return None
    return token


def _load_annotation_file(
    filename: str,
    sep: str = "\t",
) -> pd.DataFrame:
    assert os.path.exists(filename), filename
    with open(filename, "r", encoding="utf8") as infile:
        annot_df = pd.read_csv(
            infile,
            sep=sep,
            index_col=False,
            dtype={
                "chrom": str,
                "position": np.int32,
            },
            converters={
                "cshl_variant": _convert_string,
                "effects": _convert_string,
                "effect_gene_genes": _convert_array_of_strings,
                "effect_gene_types": _convert_array_of_strings,
                "effect_details_transcript_ids": _convert_array_of_strings,
                "effect_details_details": _convert_array_of_strings,
            },
            encoding="utf-8",
        ).replace({np.nan: None})
    special_columns = set(annot_df.columns) & {
        "alternative", "effect_type",
    }

    for col in special_columns:
        annot_df[col] = (
            annot_df[col]
            .astype(object)
            .where(pd.notna(annot_df[col]), None)
        )
    return annot_df


def load_stored_annotation(
    variants_loader: VariantsGenotypesLoader,
    annotation_filename: str,
) -> list[tuple[SummaryVariant, list[FamilyVariant]]]:
    """Load variants with stored annotation."""
    result: list[tuple[SummaryVariant, list[FamilyVariant]]] = []

    variant_iterator = variants_loader.full_variants_iterator()
    start = time.time()
    annot_df = _load_annotation_file(annotation_filename)

    elapsed = time.time() - start
    logger.info(
        "Storred annotation file (%s) loaded in in %.2f sec",
        annotation_filename, elapsed)

    start = time.time()
    records = annot_df.to_dict(orient="records")
    index = 0

    while index < len(records):
        sumary_variant, family_variants = next(
            variant_iterator, (None, None))
        if sumary_variant is None:
            break
        assert family_variants is not None

        variant_records = []

        current_record = records[index]
        assert "summary_index" in current_record, \
            list(current_record.keys())

        while current_record["summary_index"] == \
                sumary_variant.summary_index:
            variant_records.append(current_record)
            index += 1
            if index >= len(records):
                break
            current_record = records[index]

        assert len(variant_records) > 0, sumary_variant

        for sallele in sumary_variant.alleles:
            sallele.update_attributes(
                variant_records[sallele.allele_index])  # type: ignore
        result.append((sumary_variant, family_variants))

    elapsed = time.time() - start
    logger.info(
        "Storred annotation file (%s) parsed in %.2f sec",
        annotation_filename, elapsed)
    return result


class StoredAnnotationDecorator(AnnotationDecorator):
    """Annotate variant using a stored annotator."""

    def __init__(
        self, variants_loader: VariantsGenotypesLoader,
        annotation_filename: str,
    ) -> None:
        super().__init__(variants_loader)

        assert os.path.exists(annotation_filename)
        self.annotation_filename = annotation_filename

    @staticmethod
    def decorate(
        variants_loader: VariantsGenotypesLoader, source_filename: str,
    ) -> VariantsLoader:
        """Wrap variants_loader into a StoredAnnotationDecorator."""
        annotation_filename = StoredAnnotationDecorator \
            .build_annotation_filename(
                source_filename,
            )
        if not os.path.exists(annotation_filename):
            logger.warning("stored annotation missing %s", annotation_filename)
            return variants_loader
        return StoredAnnotationDecorator(
            variants_loader, annotation_filename,
        )

    @classmethod
    def _convert_array_of_strings(cls, token: str) -> list[str] | None:
        if not token:
            return None
        token = token.strip()
        return [w.strip() for w in token.split(cls.SEP1)]

    @staticmethod
    def _convert_string(token: str) -> str | None:
        if not token:
            return None
        return token

    @classmethod
    def _load_annotation_file(
        cls, filename: str,
        sep: str = "\t",
    ) -> pd.DataFrame:
        assert os.path.exists(filename)
        with open(filename, "r", encoding="utf8") as infile:
            annot_df = pd.read_csv(
                infile,
                sep=sep,
                index_col=False,
                dtype={
                    "chrom": str,
                    "position": np.int32,
                },
                converters={
                    "cshl_variant": cls._convert_string,
                    "effects": cls._convert_string,
                    "effect_gene_genes": cls._convert_array_of_strings,
                    "effect_gene_types": cls._convert_array_of_strings,
                    "effect_details_transcript_ids":
                    cls._convert_array_of_strings,
                    "effect_details_details": cls._convert_array_of_strings,
                },
                encoding="utf-8",
            ).replace({np.nan: None})
        special_columns = set(annot_df.columns) & {
            "alternative", "effect_type",
        }

        for col in special_columns:
            annot_df[col] = (
                annot_df[col]
                .astype(object)
                .where(pd.notna(annot_df[col]), None)
            )
        return annot_df

    def full_variants_iterator(
        self,
    ) -> FullVariantsIterator:
        variant_iterator = self.variants_loader.full_variants_iterator()
        start = time.time()
        annot_df = self._load_annotation_file(self.annotation_filename)

        elapsed = time.time() - start
        logger.info(
            "Storred annotation file (%s) loaded in in %.2f sec",
            self.annotation_filename, elapsed)

        start = time.time()
        records = annot_df.to_dict(orient="records")
        index = 0

        while index < len(records):
            sumary_variant, family_variants = next(
                variant_iterator, (None, None))
            if sumary_variant is None:
                return
            assert family_variants is not None

            variant_records = []

            current_record = records[index]
            assert "summary_index" in current_record, \
                list(current_record.keys())

            while current_record["summary_index"] == \
                    sumary_variant.summary_index:
                variant_records.append(current_record)
                index += 1
                if index >= len(records):
                    break
                current_record = records[index]

            assert len(variant_records) > 0, sumary_variant

            for sallele in sumary_variant.alleles:
                sallele.update_attributes(
                    variant_records[sallele.allele_index])  # type: ignore
            yield sumary_variant, family_variants

        elapsed = time.time() - start
        logger.info(
            "Storred annotation file (%s) parsed in %.2f sec",
            self.annotation_filename, elapsed)
