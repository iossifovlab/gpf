import os
import time
import logging
import json
import functools
from typing import Any, Optional, cast, Union

import fsspec

import pyarrow as pa
import pyarrow.parquet as pq

from dae.utils import fs_utils
from dae.parquet.helpers import url_to_pyarrow_fs
from dae.variants.attributes import Inheritance
from dae.variants.family_variant import FamilyAllele
from dae.utils.variant_utils import is_all_reference_genotype, \
    is_unknown_genotype

from dae.variants.variant import SummaryAllele
from dae.parquet.parquet_writer import \
    collect_pedigree_parquet_schema, \
    fill_family_bins, \
    append_meta_to_parquet
from dae.parquet.schema2.serializers import AlleleParquetSerializer
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.variants_loaders.raw.loader import VariantsLoader

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
        variant_loader: VariantsLoader,
        filesystem: Optional[fsspec.AbstractFileSystem] = None,
        row_groups_size: int = 50_000,
        schema: str = "schema",
        blob_column: Optional[str] = None,
    ) -> None:

        self.filepath = filepath
        annotation_schema = variant_loader.get_attribute("annotation_schema")
        extra_attributes = variant_loader.get_attribute("extra_attributes")
        self.serializer = AlleleParquetSerializer(
            annotation_schema, extra_attributes
        )

        self.schema = getattr(self.serializer, schema)

        dirname = os.path.dirname(filepath)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname, exist_ok=True)
        self.dirname = dirname

        filesystem, filepath = url_to_pyarrow_fs(filepath, filesystem)
        compression: Union[str, dict[str, str]] = self.DEFAULT_COMPRESSION
        if blob_column is not None:
            compression = {}
            for name in self.schema.names:
                compression[name] = self.DEFAULT_COMPRESSION
            compression[blob_column] = "ZSTD"
        self._writer = pq.ParquetWriter(
            filepath, self.schema,
            compression=compression,
            filesystem=filesystem,
            use_compliant_nested_type=True,
            write_page_index=True,
        )
        self.row_groups_size = row_groups_size
        self._batches: list[pa.RecordBatch] = []
        self._data: Optional[dict[str, Any]] = None
        self.data_reset()

    def data_reset(self) -> None:
        self._data = {name: [] for name in self.schema.names}

    def size(self) -> int:
        assert self._data is not None
        return max(len(val) for val in self._data.values())

    def build_table(self) -> pa.Table:
        table = pa.Table.from_batches(self._batches, self.schema)
        return table

    def build_batch(self) -> pa.RecordBatch:
        return pa.RecordBatch.from_pydict(self._data, self.schema)

    def _write_batch(self) -> None:
        batch = self.build_batch()
        self._batches.append(batch)
        self.data_reset()
        if len(self._batches) >= self.row_groups_size // self.BATCH_ROWS:
            self._flush_batches()

    def _flush_batches(self) -> None:
        if len(self._batches) == 0:
            return
        self._writer.write_table(self.build_table())
        self._batches = []

    def append_summary_allele(
            self, allele: SummaryAllele, json_data: str) -> None:
        """Append the data for an entire variant to the correct file."""
        assert self._data is not None

        data = self.serializer.build_summary_allele_batch_dict(
            allele, json_data
        )

        for k, v in self._data.items():
            v.extend(data[k])

        if self.size() >= self.BATCH_ROWS:
            logger.info(
                "parquet writer %s data flushing at len %s",
                self.filepath, self.size())
            self._write_batch()

    def append_family_allele(
            self, allele: FamilyAllele, json_data: str) -> None:
        """Append the data for an entire variant to the correct file."""
        assert self._data is not None

        data = self.serializer.build_family_allele_batch_dict(
            allele, json_data
        )

        for k, v in self._data.items():
            v.extend(data[k])

        if self.size() >= self.BATCH_ROWS:
            logger.info(
                "parquet writer %s data flushing at len %s",
                self.filepath, self.size())
            self._write_batch()

    def close(self) -> None:
        """Close the parquet writer and write any remaining data."""
        logger.info(
            "closing parquet writer %s at len %d", self.dirname, self.size())

        if self.size() > 0:
            self._write_batch()
            self._flush_batches()

        self._writer.close()


class VariantsParquetWriter:
    """Provide functions for storing variants into parquet dataset."""

    def __init__(
        self,
        out_dir: str,
        variants_loader: VariantsLoader,
        partition_descriptor: PartitionDescriptor,
        bucket_index: int = 1,
        row_groups_size: int = 50_000,
        include_reference: bool = True,
        filesystem: Optional[fsspec.AbstractFileSystem] = None,
    ) -> None:
        self.out_dir = out_dir
        self.variants_loader = variants_loader
        self.families = variants_loader.families
        self.full_variants_iterator = variants_loader.full_variants_iterator()

        self.bucket_index = bucket_index
        assert self.bucket_index < 1_000_000, "bad bucket index"

        self.row_groups_size = row_groups_size
        self.filesystem = filesystem

        self.include_reference = include_reference

        self.start = time.time()
        self.data_writers: dict[str, ContinuousParquetFileWriter] = {}
        assert isinstance(partition_descriptor, PartitionDescriptor)
        self.partition_descriptor = partition_descriptor
        fill_family_bins(
            self.families, self.partition_descriptor)

        annotation_schema = self.variants_loader.get_attribute(
            "annotation_schema"
        )
        extra_attributes = self.variants_loader.get_attribute(
            "extra_attributes"
        )
        self.serializer = AlleleParquetSerializer(
            annotation_schema, extra_attributes
        )

    def _build_family_filename(
        self, allele: FamilyAllele,
        seen_as_denovo: bool
    ) -> str:
        partition = self.partition_descriptor.family_partition(
            allele, seen_as_denovo)
        partition_directory = self.partition_descriptor.partition_directory(
            fs_utils.join(self.out_dir, "family"), partition)
        partition_filename = self.partition_descriptor.partition_filename(
            "family", partition, self.bucket_index)
        return fs_utils.join(partition_directory, partition_filename)

    def _build_summary_filename(
        self, allele: SummaryAllele,
        seen_as_denovo: bool
    ) -> str:
        partition = self.partition_descriptor.summary_partition(
            allele, seen_as_denovo)
        partition_directory = self.partition_descriptor.partition_directory(
            fs_utils.join(self.out_dir, "summary"), partition)
        partition_filename = self.partition_descriptor.partition_filename(
            "summary", partition, self.bucket_index)
        return fs_utils.join(partition_directory, partition_filename)

    def _get_bin_writer_family(
        self, allele: FamilyAllele,
        seen_as_denovo: bool
    ) -> ContinuousParquetFileWriter:
        filename = self._build_family_filename(allele, seen_as_denovo)

        if filename not in self.data_writers:
            self.data_writers[filename] = ContinuousParquetFileWriter(
                filename,
                self.variants_loader,
                filesystem=self.filesystem,
                row_groups_size=self.row_groups_size,
                schema="schema_family",
                blob_column="family_variant_data",
            )

        return self.data_writers[filename]

    def _get_bin_writer_summary(
        self, allele: SummaryAllele,
        seen_as_denovo: bool
    ) -> ContinuousParquetFileWriter:
        filename = self._build_summary_filename(allele, seen_as_denovo)

        if filename not in self.data_writers:
            self.data_writers[filename] = ContinuousParquetFileWriter(
                filename,
                self.variants_loader,
                filesystem=self.filesystem,
                row_groups_size=self.row_groups_size,
                schema="schema_summary",
                blob_column="summary_variant_data",
            )

        return self.data_writers[filename]

    def _calc_sj_index(self, summary_index: int, allele_index: int) -> int:
        assert allele_index < 10_000, "too many alleles"
        sj_index = (
            self.bucket_index * 1_000_000_000
            + summary_index) * 10_000 + allele_index
        return sj_index

    def _calc_sj_base_index(self, summary_index: int) -> int:
        sj_index = (
            self.bucket_index * 1_000_000_000
            + summary_index) * 10_000
        return sj_index

    def _write_internal(self) -> list[str]:
        # pylint: disable=too-many-locals,too-many-branches
        family_variant_index = 0
        summary_variant_index = 0
        for summary_variant_index, (
            summary_variant,
            family_variants,
        ) in enumerate(self.full_variants_iterator):
            assert summary_variant_index < 1_000_000_000, \
                "too many summary variants"
            num_fam_alleles_written = 0
            seen_in_status = summary_variant.allele_count * [0]
            seen_as_denovo = summary_variant.allele_count * [False]
            family_variants_count = summary_variant.allele_count * [0]
            sj_base_index = self._calc_sj_base_index(summary_variant_index)

            for fv in family_variants:
                family_variant_index += 1
                assert fv.gt is not None

                if is_all_reference_genotype(fv.gt) and \
                        not self.include_reference:
                    continue

                fv.summary_index = summary_variant_index
                fv.family_index = family_variant_index

                allele_indexes = set()
                for fa in fv.alleles:
                    assert fa.allele_index not in allele_indexes
                    allele_indexes.add(fa.allele_index)

                    extra_atts = {
                        "bucket_index": self.bucket_index,
                        "family_index": family_variant_index,
                        "sj_index": sj_base_index + fa.allele_index,
                    }
                    fa.update_attributes(extra_atts)

                family_variant_data_json = json.dumps(fv.to_record(),
                                                      sort_keys=True)
                family_alleles = []
                if is_unknown_genotype(fv.gt):
                    assert fv.ref_allele.allele_index == 0
                    family_alleles.append(fv.ref_allele)
                    num_fam_alleles_written += 1
                elif is_all_reference_genotype(fv.gt):
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

                    family_bin_writer = self._get_bin_writer_family(fa, sad)
                    family_bin_writer.append_family_allele(
                        fa, family_variant_data_json
                    )

                    family_variants_count[fa.allele_index] += 1
                    num_fam_alleles_written += 1

            # don't store summary alleles withouth family ones
            if num_fam_alleles_written > 0:
                summary_variant.update_attributes({
                    "seen_in_status": seen_in_status[1:],
                    "seen_as_denovo": seen_as_denovo[1:],
                    "family_variants_count": family_variants_count[1:],
                    "family_alleles_count": family_variants_count[1:],
                })
                summary_blobs_json = json.dumps(
                    summary_variant.to_record(), sort_keys=True
                )
                for summary_allele in summary_variant.alleles:
                    sj_index = sj_base_index + summary_allele.allele_index
                    extra_atts = {
                        "bucket_index": self.bucket_index,
                        "sj_index": sj_index,
                    }
                    summary_allele.summary_index = summary_variant_index
                    summary_allele.update_attributes(extra_atts)
                    summary_writer = self._get_bin_writer_summary(
                        summary_allele,
                        seen_as_denovo[summary_allele.allele_index])
                    summary_writer.append_summary_allele(
                        summary_allele, summary_blobs_json)

            if summary_variant_index % 1000 == 0 and summary_variant_index > 0:
                elapsed = time.time() - self.start
                logger.info(
                    "progress bucked %s; "
                    "summary variants: %s; family variants: %s; "
                    "elapsed time: %0.2f sec",
                    self.bucket_index,
                    summary_variant_index, family_variant_index,
                    elapsed)

        filenames = list(self.data_writers.keys())

        for bin_writer in self.data_writers.values():
            bin_writer.close()

        elapsed = time.time() - self.start
        logger.info(
            "finished bucked %s; summary variants: %s; family variants: %s; "
            "elapsed time: %0.2f sec",
            self.bucket_index, summary_variant_index, family_variant_index,
            elapsed)
        return filenames

    def write_metadata(self) -> None:
        """Write dataset metadata."""
        schema = [
            (f.name, f.type) for f in self.serializer.schema_summary
        ]
        schema.extend(
            list(self.partition_descriptor.dataset_summary_partition()))
        schema_summary = "\n".join([
            f"{n}|{t}" for n, t in schema
        ])

        schema = [
            (f.name, f.type) for f in self.serializer.schema_family
        ]
        schema.extend(
            list(self.partition_descriptor.dataset_family_partition())
        )
        schema_family = "\n".join([
            f"{n}|{t}" for n, t in schema
        ])

        extra_attributes = self.serializer.extra_attributes

        pedigree_schema = collect_pedigree_parquet_schema(
            self.families.ped_df)
        schema_pedigree = "\n".join([
            f"{f.name}|{f.type}" for f in pedigree_schema])

        metapath = fs_utils.join(self.out_dir, "meta", "meta.parquet")
        append_meta_to_parquet(
            metapath,
            key=[
                "partition_description",
                "summary_schema",
                "family_schema",
                "pedigree_schema",
                "extra_attributes",
            ],
            value=[
                self.partition_descriptor.serialize(),
                str(schema_summary),
                str(schema_family),
                str(schema_pedigree),
                str(extra_attributes),
            ]
        )

    def write_dataset(self) -> list[str]:
        filenames = self._write_internal()
        return filenames
