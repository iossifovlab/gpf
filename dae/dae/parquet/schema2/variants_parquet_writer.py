from __future__ import annotations

import functools
import logging
import os
import pathlib
import time
from collections.abc import Sequence
from contextlib import AbstractContextManager
from types import TracebackType
from typing import cast

import pyarrow as pa
import pyarrow.parquet as pq

from dae.annotation.annotation_pipeline import (
    AttributeInfo,
)
from dae.parquet.helpers import url_to_pyarrow_fs
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.parquet.schema2.serializers import (
    AlleleParquetSerializer,
    FamilyAlleleParquetSerializer,
    SummaryAlleleParquetSerializer,
    VariantsDataSerializer,
    build_summary_blob_schema,
)
from dae.utils import fs_utils
from dae.utils.processing_pipeline import Filter
from dae.utils.variant_utils import (
    is_all_reference_genotype,
    is_unknown_genotype,
)
from dae.variants.attributes import Inheritance
from dae.variants.family_variant import FamilyAllele, FamilyVariant
from dae.variants.variant import (
    SummaryAllele,
    SummaryVariant,
)
from dae.variants_loaders.raw.loader import (
    FullVariant,
)

logger = logging.getLogger(__name__)


class ContinuousParquetFileWriter:
    """A continous parquet writer.

    Class that automatically writes to a given parquet file when supplied
    enough data. Automatically dumps leftover data when closing into the file
    """

    DEFAULT_COMPRESSION = "SNAPPY"

    def __init__(
        self,
        filepath: str,
        allele_serializer: AlleleParquetSerializer,
        row_group_size: int = 10_000,
    ) -> None:

        self.filepath = filepath
        self.serializer = allele_serializer

        self.schema = self.serializer.schema()

        dirname = os.path.dirname(filepath)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname, exist_ok=True)
        self.dirname = dirname

        filesystem, filepath = url_to_pyarrow_fs(filepath)
        compression: str | dict[str, str] = self.DEFAULT_COMPRESSION

        blob_column = self.serializer.blob_column()
        if blob_column is not None:
            compression = {}
            for name in self.schema.names:
                compression[name] = self.DEFAULT_COMPRESSION
            compression[blob_column] = "ZSTD"

        self._writer = pq.ParquetWriter(
            filepath, self.schema,
            compression=compression,  # type: ignore
            filesystem=filesystem,
            use_compliant_nested_type=True,
            write_page_index=True,
        )
        self.row_group_size = row_group_size
        self._data: dict[str, list]
        self._data_reset()

    def _data_reset(self) -> None:
        self._data = {name: [] for name in self.schema.names}

    def size(self) -> int:
        return len(self._data["bucket_index"])

    def _flush(self) -> None:
        if self.size() == 0:
            return

        batch = pa.RecordBatch.from_pydict(self._data, self.schema)
        table = pa.Table.from_batches([batch], self.schema)
        self._writer.write_table(table)

    def append_allele(
        self, allele: SummaryAllele | FamilyAllele,
        variant_blob: bytes,
    ) -> None:
        """Append the data for entire allele to the correct partition file."""
        assert self._data is not None

        data = self.serializer.build_allele_record_dict(
            allele, variant_blob,
        )

        for k, v in self._data.items():
            v.append(data[k])

        if self.size() >= self.row_group_size:
            logger.debug(
                "parquet writer %s create summary batch at len %s",
                self.filepath, self.size())
            self._flush()
            self._data_reset()

    def close(self) -> None:
        """Close the parquet writer and write any remaining data."""
        logger.debug(
            "closing parquet writer %s with %d rows",
            self.filepath, self.size())

        self._flush()
        self._writer.close()


class VariantsParquetWriter(AbstractContextManager):
    """Provide functions for storing variants into parquet dataset."""

    def __init__(
        self,
        out_dir: pathlib.Path | str,
        annotation_schema: list[AttributeInfo],
        partition_descriptor: PartitionDescriptor,
        *,
        blob_serializer: VariantsDataSerializer | None = None,
        bucket_index: int = 1,
        row_group_size: int = 10_000,
        include_reference: bool = False,
        variants_blob_serializer: str = "json",
    ) -> None:
        self.out_dir = str(out_dir)

        self.bucket_index = bucket_index
        assert self.bucket_index < 1_000_000, "bad bucket index"

        self.row_group_size = row_group_size

        self.include_reference = include_reference

        self.start = time.time()
        self.data_writers: dict[str, ContinuousParquetFileWriter] = {}
        assert isinstance(partition_descriptor, PartitionDescriptor)
        self.partition_descriptor = partition_descriptor
        self.annotation_schema = annotation_schema

        self.summary_serializer = SummaryAlleleParquetSerializer(
            self.annotation_schema,
        )
        self.family_serializer = FamilyAlleleParquetSerializer(
            self.annotation_schema,
        )

        if blob_serializer is None:
            blob_serializer = VariantsDataSerializer.build_serializer(
                build_summary_blob_schema(
                    self.annotation_schema,
                ),
                serializer_type=variants_blob_serializer,
            )
        self.blob_serializer = blob_serializer
        self.summary_index = 0
        self.family_index = 0

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            exc_tb: TracebackType | None) -> bool:
        self.close()
        if exc_type is not None:
            logger.error(
                "exception during annotation: %s, %s, %s",
                exc_type, exc_value, exc_tb)
        return True

    def _build_family_filename(
        self, allele: FamilyAllele, *,
        seen_as_denovo: bool,
    ) -> str:
        partition = self.partition_descriptor.family_partition(
            allele, seen_as_denovo=seen_as_denovo)
        partition_directory = self.partition_descriptor.partition_directory(
            fs_utils.join(self.out_dir, "family"), partition)
        partition_filename = self.partition_descriptor.partition_filename(
            "family", partition, self.bucket_index)
        return fs_utils.join(partition_directory, partition_filename)

    def _build_summary_filename(
        self, allele: SummaryAllele, *,
        seen_as_denovo: bool,
    ) -> str:
        partition = self.partition_descriptor.summary_partition(
            allele, seen_as_denovo=seen_as_denovo)
        partition_directory = self.partition_descriptor.partition_directory(
            fs_utils.join(self.out_dir, "summary"), partition)
        partition_filename = self.partition_descriptor.partition_filename(
            "summary", partition, self.bucket_index)
        return fs_utils.join(partition_directory, partition_filename)

    def _get_bin_writer_family(
        self, allele: FamilyAllele, *,
        seen_as_denovo: bool,
    ) -> ContinuousParquetFileWriter:
        filename = self._build_family_filename(
            allele, seen_as_denovo=seen_as_denovo)

        if filename not in self.data_writers:
            self.data_writers[filename] = ContinuousParquetFileWriter(
                filename,
                self.family_serializer,
                row_group_size=self.row_group_size,
            )

        return self.data_writers[filename]

    def _get_bin_writer_summary(
        self, allele: SummaryAllele, *,
        seen_as_denovo: bool,
    ) -> ContinuousParquetFileWriter:
        filename = self._build_summary_filename(
            allele, seen_as_denovo=seen_as_denovo)

        if filename not in self.data_writers:
            self.data_writers[filename] = ContinuousParquetFileWriter(
                filename,
                self.summary_serializer,
                row_group_size=self.row_group_size,
            )

        return self.data_writers[filename]

    def _calc_sj_base_index(self, summary_index: int) -> int:
        return (
            self.bucket_index * 1_000_000_000
            + summary_index) * 10_000

    def write(
        self, data: FullVariant,
    ) -> None:
        """Consume a single full variant."""
        summary_index = self.summary_index
        sj_base_index = self._calc_sj_base_index(summary_index)
        family_index, num_fam_alleles_written = \
            self._write_family_variants(
                self.family_index, summary_index, sj_base_index,
                data.summary_variant,
                data.family_variants,
            )
        if num_fam_alleles_written > 0:
            self.write_summary_variant(
                data.summary_variant,
                sj_base_index=sj_base_index,
            )

        self.summary_index += 1
        self.family_index = family_index

    def _write_family_variants(
            self, family_index: int,
            summary_index: int,
            sj_base_index: int,
            summary_variant: SummaryVariant,
            family_variants: Sequence[FamilyVariant],
    ) -> tuple[int, int]:
        num_fam_alleles_written = 0
        seen_in_status = summary_variant.allele_count * [0]
        seen_as_denovo = summary_variant.allele_count * [False]
        family_variants_count = summary_variant.allele_count * [0]

        for fv in family_variants:
            family_index += 1
            assert fv.gt is not None

            if is_all_reference_genotype(fv.gt) and \
                    not self.include_reference:
                continue
            fv.summary_index = summary_index
            fv.family_index = family_index

            allele_indexes = set()
            for fa in fv.alleles:
                assert fa.allele_index not in allele_indexes
                allele_indexes.add(fa.allele_index)

                extra_atts = {
                        "bucket_index": self.bucket_index,
                        "family_index": family_index,
                        "sj_index": sj_base_index + fa.allele_index,
                    }
                fa.update_attributes(extra_atts)

            family_variant_blob = \
                self.blob_serializer.serialize_family(fv)

            denovo_reference = any(
                i == Inheritance.denovo
                for i in cast(
                    FamilyAllele, fv.ref_allele).inheritance_in_members)

            family_alleles = []
            if is_unknown_genotype(fv.gt) or \
                    is_all_reference_genotype(fv.gt):
                assert fv.ref_allele.allele_index == 0
                family_alleles.append(fv.ref_allele)
                num_fam_alleles_written += 1
            elif self.include_reference or denovo_reference:
                family_alleles.append(fv.ref_allele)

            family_alleles.extend(fv.alt_alleles)

            for aa in family_alleles:
                fa = cast(FamilyAllele, aa)
                seen_in_status[fa.allele_index] = functools.reduce(
                        lambda t, s: t | s.value,
                        filter(None, fa.allele_in_statuses),
                        seen_in_status[fa.allele_index])
                inheritance = list(
                        filter(
                            lambda v: v not in {
                                None,
                                Inheritance.unknown, Inheritance.missing},
                            fa.inheritance_in_members))

                sad = any(
                        i == Inheritance.denovo
                        for i in inheritance)

                seen_as_denovo[fa.allele_index] = \
                    sad or seen_as_denovo[fa.allele_index]

                family_bin_writer = self._get_bin_writer_family(
                    fa, seen_as_denovo=sad)
                assert isinstance(
                    family_bin_writer.serializer,
                    FamilyAlleleParquetSerializer)

                family_bin_writer.append_allele(
                    fa, family_variant_blob)

                family_variants_count[fa.allele_index] += 1
                num_fam_alleles_written += 1

        # don't store summary alleles withouth family ones
        if num_fam_alleles_written > 0:
            summary_variant.summary_index = summary_index
            summary_variant.ref_allele.update_attributes(
                    {"bucket_index": self.bucket_index})
            summary_variant.update_attributes({
                    "seen_in_status": seen_in_status[1:],
                    "seen_as_denovo": seen_as_denovo[1:],
                    "family_variants_count": family_variants_count[1:],
                    "family_alleles_count": family_variants_count[1:],
                    "bucket_index": [self.bucket_index],
                })
        return family_index, num_fam_alleles_written

    def close(self) -> None:
        for bin_writer in self.data_writers.values():
            bin_writer.close()

    def write_summary_variant(
        self, summary_variant: SummaryVariant,
        sj_base_index: int | None = None,
    ) -> None:
        """Write a single summary variant to the correct parquet file."""
        if sj_base_index is not None:
            for summary_allele in summary_variant.alleles:
                assert summary_allele.allele_index < 10_000, "too many alleles"

                sj_index = sj_base_index + summary_allele.allele_index
                extra_atts = {
                    "sj_index": sj_index,
                }
                summary_allele.update_attributes(extra_atts)
        summary_blobs_json = self.blob_serializer.serialize_summary(
            summary_variant)
        if self.include_reference:
            stored_alleles = summary_variant.alleles
        else:
            stored_alleles = summary_variant.alt_alleles

        for summary_allele in stored_alleles:
            seen_as_denovo = summary_allele.get_attribute("seen_as_denovo")
            summary_writer = self._get_bin_writer_summary(
                summary_allele, seen_as_denovo=seen_as_denovo)
            summary_writer.append_allele(
                summary_allele, summary_blobs_json)


class Schema2VariantConsumer(Filter):
    """Consumer for Parquet summary variants."""
    def __init__(self, writer: VariantsParquetWriter):
        self.writer = writer

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        if exc_type is not None:
            logger.error(
                "exception during annotation: %s, %s, %s",
                exc_type, exc_value, exc_tb)

        self.writer.__exit__(exc_type, exc_value, exc_tb)

        return exc_type is not None

    def filter(self, data: FullVariant) -> None:
        self.writer.write(data)


class Schema2VariantBatchConsumer(Filter):
    """Consumer for Parquet summary variants."""
    def __init__(self, writer: VariantsParquetWriter):
        self.writer = writer

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        if exc_type is not None:
            logger.error(
                "exception during annotation: %s, %s, %s",
                exc_type, exc_value, exc_tb)

        self.writer.__exit__(exc_type, exc_value, exc_tb)

        return exc_type is not None

    def filter(self, data: Sequence[FullVariant]) -> None:
        for variant in data:
            self.writer.write(variant)


class Schema2SummaryVariantConsumer(Filter):
    """Consumer for Parquet summary variants."""
    def __init__(self, writer: VariantsParquetWriter):
        self.writer = writer

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        if exc_type is not None:
            logger.error(
                "exception during annotation: %s, %s, %s",
                exc_type, exc_value, exc_tb)

        self.writer.__exit__(exc_type, exc_value, exc_tb)

        return exc_type is not None

    def filter(self, data: FullVariant) -> None:
        self.writer.write_summary_variant(data.summary_variant)


class Schema2SummaryVariantBatchConsumer(Filter):
    """Consumer for Parquet summary variants."""
    def __init__(self, writer: VariantsParquetWriter):
        self.writer = writer

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        if exc_type is not None:
            logger.error(
                "exception during annotation: %s, %s, %s",
                exc_type, exc_value, exc_tb)

        self.writer.__exit__(exc_type, exc_value, exc_tb)

        return exc_type is not None

    def filter(self, data: Sequence[FullVariant]) -> None:
        for variant in data:
            self.writer.write_summary_variant(variant.summary_variant)
