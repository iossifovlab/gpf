from __future__ import annotations

import logging
import os
import time

import numpy as np
import pandas as pd

from dae.import_tools.annotation_decorators import AnnotationDecorator
from dae.variants_loaders.raw.loader import (
    FullVariantsIterator,
    VariantsGenotypesLoader,
    VariantsLoader,
)

logger = logging.getLogger(__name__)


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
