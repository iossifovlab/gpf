import functools
import logging
import os
import time
from collections.abc import Iterator
from typing import Any, Optional, Union, cast

import fsspec
import pyarrow as pa
import pyarrow.parquet as pq

from dae.annotation.annotation_pipeline import AttributeInfo
from dae.parquet.helpers import url_to_pyarrow_fs
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.parquet.schema2.serializers import AlleleParquetSerializer
from dae.parquet.schema2.variant_serializers import (
    VariantsDataSerializer,
    ZstdIndexedVariantsDataSerializer,
)
from dae.utils import fs_utils
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

logger = logging.getLogger(__name__)


class ContinuousParquetFileWriter:
    """A continous parquet writer.

    Class that automatically writes to a given parquet file when supplied
    enough data. Automatically dumps leftover data when closing into the file
    """

    BATCH_ROWS = 1_000
    DEFAULT_COMPRESSION = "SNAPPY"

    def __init__(
        self,
        filepath: str,
        annotation_schema: list[AttributeInfo],
        filesystem: Optional[fsspec.AbstractFileSystem] = None,
        row_group_size: int = 10_000,
        schema: str = "schema",
    ) -> None:

        self.filepath = filepath
        self.annotation_schema = annotation_schema
        self.serializer = AlleleParquetSerializer(
            self.annotation_schema,
        )

        self.schema = getattr(self.serializer, schema)

        dirname = os.path.dirname(filepath)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname, exist_ok=True)
        self.dirname = dirname

        filesystem, filepath = url_to_pyarrow_fs(filepath, filesystem)
        compression: Union[str, dict[str, str]] = self.DEFAULT_COMPRESSION

        self._writer = pq.ParquetWriter(
            filepath, self.schema,
            compression=compression,
            filesystem=filesystem,
            use_compliant_nested_type=True,
            write_page_index=True,
        )
        self.row_group_size = row_group_size
        self._batches: list[pa.RecordBatch] = []
        self._data: Optional[dict[str, Any]] = None
        self.data_reset()

    def data_reset(self) -> None:
        self._data = {name: [] for name in self.schema.names}

    def size(self) -> int:
        assert self._data is not None
        return len(self._data["bucket_index"])

    def build_table(self) -> pa.Table:
        logger.info(
            "writing %s rows to parquet %s",
            sum(len(b) for b in self._batches),
            self.filepath)
        return pa.Table.from_batches(self._batches, self.schema)

    def build_batch(self) -> pa.RecordBatch:
        return pa.RecordBatch.from_pydict(self._data, self.schema)

    def _write_batch(self) -> None:
        if self.size() == 0:
            return
        batch = self.build_batch()
        self._batches.append(batch)
        self.data_reset()
        if len(self._batches) >= self.row_group_size // self.BATCH_ROWS:
            self._flush_batches()

    def _flush_batches(self) -> None:
        if len(self._batches) == 0:
            return
        logger.debug(
            "flushing %s batches", len(self._batches))
        self._writer.write_table(self.build_table())
        self._batches = []

    def append_summary_allele(
            self, allele: SummaryAllele, json_data: bytes) -> None:
        """Append the data for an entire variant to the correct file."""
        assert self._data is not None

        data = self.serializer.build_summary_allele_batch_dict(
            allele, json_data,
        )

        for k, v in self._data.items():
            v.append(data[k])

        if self.size() >= self.BATCH_ROWS:
            logger.debug(
                "parquet writer %s create summary batch at len %s",
                self.filepath, self.size())
            self._write_batch()

    def append_family_allele(
            self, allele: FamilyAllele, json_data: bytes) -> None:
        """Append the data for an entire variant to the correct file."""
        assert self._data is not None

        data = self.serializer.build_family_allele_batch_dict(
            allele, json_data,
        )

        for k, v in self._data.items():
            v.extend(data[k])

        if self.size() >= self.BATCH_ROWS:
            logger.debug(
                "parquet writer %s create family batch at len %s",
                self.filepath, self.size())
            self._write_batch()

    def close(self) -> None:
        """Close the parquet writer and write any remaining data."""
        logger.debug(
            "closing parquet writer %s with %d rows",
            self.filepath, self.size())

        self._write_batch()
        self._flush_batches()
        self._writer.close()


class VariantsParquetWriter:
    """Provide functions for storing variants into parquet dataset."""

    def __init__(
        self,
        out_dir: str,
        annotation_schema: list[AttributeInfo],
        partition_descriptor: PartitionDescriptor,
        *,
        serializer: Optional[VariantsDataSerializer] = None,
        bucket_index: int = 1,
        row_group_size: int = 10_000,
        include_reference: bool = True,
        filesystem: Optional[fsspec.AbstractFileSystem] = None,
    ) -> None:
        self.out_dir = out_dir

        if serializer is None:
            annotation_fields = [
                a.name for a in annotation_schema
                if not a.internal
            ]
            meta = ZstdIndexedVariantsDataSerializer.build_serialization_meta(
                annotation_fields)
            serializer = VariantsDataSerializer.build_serializer(meta)
        self.serializer = serializer

        self.bucket_index = bucket_index
        assert self.bucket_index < 1_000_000, "bad bucket index"

        self.row_group_size = row_group_size
        self.filesystem = filesystem

        self.include_reference = include_reference

        self.start = time.time()
        self.data_writers: dict[str, ContinuousParquetFileWriter] = {}
        assert isinstance(partition_descriptor, PartitionDescriptor)
        self.partition_descriptor = partition_descriptor
        self.annotation_schema = annotation_schema

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
                self.annotation_schema,
                filesystem=self.filesystem,
                row_group_size=self.row_group_size,
                schema="schema_family",
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
                self.annotation_schema,
                filesystem=self.filesystem,
                row_group_size=self.row_group_size,
                schema="schema_summary",
            )

        return self.data_writers[filename]

    def _calc_sj_index(self, summary_index: int, allele_index: int) -> int:
        assert allele_index < 10_000, "too many alleles"
        return (
            self.bucket_index * 1_000_000_000
            + summary_index) * 10_000 + allele_index

    def _calc_sj_base_index(self, summary_index: int) -> int:
        return (
            self.bucket_index * 1_000_000_000
            + summary_index) * 10_000

    def write_dataset(
        self,
        full_variants_iterator: Iterator[
            tuple[SummaryVariant, list[FamilyVariant]]],
    ) -> list[str]:
        """Write variant to partitioned parquet dataset."""
        # pylint: disable=too-many-locals,too-many-branches
        family_index = 0
        summary_index = 0
        for summary_index, (
            summary_variant,
            family_variants,
        ) in enumerate(full_variants_iterator):
            assert summary_index < 1_000_000_000, \
                "too many summary variants"
            num_fam_alleles_written = 0
            seen_in_status = summary_variant.allele_count * [0]
            seen_as_denovo = summary_variant.allele_count * [False]
            family_variants_count = summary_variant.allele_count * [0]
            sj_base_index = self._calc_sj_base_index(summary_index)

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

                family_variant_data_json = self.serializer.serialize_family(fv)

                family_alleles = []
                if is_unknown_genotype(fv.gt) or \
                        is_all_reference_genotype(fv.gt):
                    assert fv.ref_allele.allele_index == 0
                    family_alleles.append(fv.ref_allele)
                    num_fam_alleles_written += 1
                elif self.include_reference:
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
                    family_bin_writer.append_family_allele(
                        fa, family_variant_data_json,
                    )

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
                self.write_summary_variant(
                    summary_variant, sj_base_index=sj_base_index,
                )

            if summary_index % 1000 == 0 and summary_index > 0:
                elapsed = time.time() - self.start
                logger.info(
                    "progress bucked %s; "
                    "summary variants: %s; family variants: %s; "
                    "elapsed time: %0.2f sec",
                    self.bucket_index,
                    summary_index, family_index,
                    elapsed)

        filenames = list(self.data_writers.keys())

        self.close()

        elapsed = time.time() - self.start
        logger.info(
            "finished bucked %s; summary variants: %s; family variants: %s; "
            "elapsed time: %0.2f sec",
            self.bucket_index, summary_index, family_index,
            elapsed)
        return filenames

    def close(self) -> None:
        for bin_writer in self.data_writers.values():
            bin_writer.close()

    def write_summary_variant(
        self, summary_variant: SummaryVariant,
        attributes: Optional[dict[str, Any]] = None,
        sj_base_index: Optional[int] = None,
    ) -> None:
        """Write a single summary variant to the correct parquet file."""
        if attributes is not None:
            summary_variant.update_attributes(attributes)
        if sj_base_index is not None:
            for summary_allele in summary_variant.alleles:
                sj_index = sj_base_index + summary_allele.allele_index
                extra_atts = {
                    "sj_index": sj_index,
                }
                summary_allele.update_attributes(extra_atts)
        summary_blobs_json = self.serializer.serialize_summary(summary_variant)
        if self.include_reference:
            stored_alleles = summary_variant.alleles
        else:
            stored_alleles = summary_variant.alt_alleles

        for summary_allele in stored_alleles:
            seen_as_denovo = summary_allele.get_attribute("seen_as_denovo")
            summary_writer = self._get_bin_writer_summary(
                summary_allele, seen_as_denovo=seen_as_denovo)
            summary_writer.append_summary_allele(
                summary_allele, summary_blobs_json)
