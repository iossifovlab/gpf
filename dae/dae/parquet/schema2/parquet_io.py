import os
import sys
import time
import logging
import json
from functools import reduce
from typing import Any, Optional
import toml

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
from dae.parquet.schema2.serializers import AlleleParquetSerializer
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.variants_loaders.raw.loader import VariantsLoader

logger = logging.getLogger(__name__)


class ContinuousParquetFileWriter:
    """A continous parquet writer.

    Class that automatically writes to a given parquet file when supplied
    enough data. Automatically dumps leftover data when closing into the file
    """

    def __init__(
        self,
        filepath: str,
        variant_loader: VariantsLoader,
        filesystem: Optional[fsspec.AbstractFileSystem] = None,
        rows: int = 100_000,
        schema: str = "schema",
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
        self._writer = pq.ParquetWriter(
            filepath, self.schema, compression="snappy", filesystem=filesystem,
            version="1.0", use_compliant_nested_type=True
        )
        self.rows = rows
        self._data: Optional[dict[str, Any]] = None
        self.data_reset()

    def data_reset(self) -> None:
        self._data = {name: [] for name in self.schema.names}

    def size(self) -> int:
        assert self._data is not None
        return max(len(val) for val in self._data.values())

    def build_table(self) -> pa.Table:
        table = pa.Table.from_pydict(self._data, self.schema)
        return table

    def _write_table(self) -> None:
        self._writer.write_table(self.build_table())
        self.data_reset()

    def append_summary_allele(
            self, allele: SummaryAllele, json_data: str) -> None:
        """Append the data for an entire variant to the correct file."""
        assert self._data is not None

        data = self.serializer.build_summary_allele_batch_dict(
            allele, json_data
        )

        for k, v in self._data.items():
            v.extend(data[k])

        if self.size() >= self.rows:
            logger.info(
                "parquet writer %s data flushing at len %s",
                self.filepath, self.size())
            self._write_table()

    def append_family_allele(
            self, allele: FamilyAllele, json_data: str) -> None:
        """Append the data for an entire variant to the correct file."""
        assert self._data is not None

        data = self.serializer.build_family_allele_batch_dict(
            allele, json_data
        )

        for k, v in self._data.items():
            v.extend(data[k])

        if self.size() >= self.rows:
            logger.info(
                "parquet writer %s data flushing at len %s",
                self.filepath, self.size())
            self._write_table()

    def close(self) -> None:
        logger.info(
            "closing parquet writer %s at len %d", self.dirname, self.size())

        if self.size() > 0:
            self._write_table()
        self._writer.close()


class VariantsParquetWriter:
    """Provide functions for storing variants into parquet dataset."""

    def __init__(
        self,
        out_dir: str,
        variants_loader: VariantsLoader,
        partition_descriptor: PartitionDescriptor,
        bucket_index: int = 1,
        rows: int = 100_000,
        include_reference: bool = True,
        filesystem: Optional[fsspec.AbstractFileSystem] = None,
    ) -> None:
        self.out_dir = out_dir
        self.variants_loader = variants_loader
        self.families = variants_loader.families
        self.full_variants_iterator = variants_loader.full_variants_iterator()

        self.bucket_index = bucket_index
        self.rows = rows
        self.filesystem = filesystem

        self.include_reference = include_reference

        self.start = time.time()
        self.data_writers: dict[str, ContinuousParquetFileWriter] = {}
        assert isinstance(partition_descriptor, PartitionDescriptor)
        self.partition_descriptor = partition_descriptor

        annotation_schema = self.variants_loader.get_attribute(
            "annotation_schema"
        )
        extra_attributes = self.variants_loader.get_attribute(
            "extra_attributes"
        )
        self.serializer = AlleleParquetSerializer(
            annotation_schema, extra_attributes
        )

    def _build_family_filename(self, allele: FamilyAllele) -> str:
        partition = self.partition_descriptor.family_partition(allele)
        partition_directory = self.partition_descriptor.partition_directory(
            fs_utils.join(self.out_dir, "family"), partition)
        partition_filename = self.partition_descriptor.partition_filename(
            "family", partition, self.bucket_index)
        return fs_utils.join(partition_directory, partition_filename)

    def _build_summary_filename(self, allele: SummaryAllele) -> str:
        partition = self.partition_descriptor.summary_partition(allele)
        partition_directory = self.partition_descriptor.partition_directory(
            fs_utils.join(self.out_dir, "summary"), partition)
        partition_filename = self.partition_descriptor.partition_filename(
            "summary", partition, self.bucket_index)
        return fs_utils.join(partition_directory, partition_filename)

    def _get_bin_writer_family(
            self, allele: FamilyAllele) -> ContinuousParquetFileWriter:
        filename = self._build_family_filename(allele)

        if filename not in self.data_writers:
            self.data_writers[filename] = ContinuousParquetFileWriter(
                filename,
                self.variants_loader,
                filesystem=self.filesystem,
                rows=self.rows,
                schema="schema_family",
            )

        return self.data_writers[filename]

    def _get_bin_writer_summary(
            self, allele: SummaryAllele) -> ContinuousParquetFileWriter:
        filename = self._build_summary_filename(allele)

        if filename not in self.data_writers:
            self.data_writers[filename] = ContinuousParquetFileWriter(
                filename,
                self.variants_loader,
                filesystem=self.filesystem,
                rows=self.rows,
                schema="schema_summary",
            )

        return self.data_writers[filename]

    def _write_internal(self) -> list[str]:
        # pylint: disable=too-many-locals
        family_variant_index = 0

        for summary_variant_index, (
            summary_variant,
            family_variants,
        ) in enumerate(self.full_variants_iterator):
            num_fam_alleles_written = 0
            seen_in_status = summary_variant.allele_count * [0]
            seen_as_denovo = summary_variant.allele_count * [False]
            family_variants_count = summary_variant.allele_count * [0]

            for fv in family_variants:
                family_variant_index += 1

                if is_all_reference_genotype(fv.gt) and \
                        not self.include_reference:
                    continue

                fv.summary_index = summary_variant_index
                fv.family_index = family_variant_index

                for fa in fv.alleles:
                    extra_atts = {
                        "bucket_index": self.bucket_index,
                        "family_index": family_variant_index,
                    }
                    fa.update_attributes(extra_atts)

                family_variant_data_json = json.dumps(fv.to_record(),
                                                      sort_keys=True)
                family_alleles = []
                if is_unknown_genotype(fv.gt):
                    family_alleles.append(fv.ref_allele)
                    num_fam_alleles_written += 1
                elif is_all_reference_genotype(fv.gt):
                    family_alleles.append(fv.ref_allele)
                    num_fam_alleles_written += 1
                elif self.include_reference:
                    family_alleles.append(fv.ref_allele)

                family_alleles.extend(fv.alt_alleles)
                for fa in family_alleles:
                    family_bin_writer = self._get_bin_writer_family(fa)
                    family_bin_writer.append_family_allele(
                        fa, family_variant_data_json
                    )
                    seen_in_status[fa.allele_index] = reduce(
                        lambda t, s: t | s.value,  # type: ignore
                        filter(None, fa.allele_in_statuses),
                        seen_in_status[fa.allele_index])
                    seen_as_denovo[fa.allele_index] = reduce(
                        lambda t, s: t or (s == Inheritance.denovo),
                        filter(None, fa.inheritance_in_members),
                        seen_as_denovo[fa.allele_index])
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
                # build summary json blob (concat all other alleles)
                # INSIDE summary_variant
                summary_blobs_json = json.dumps(
                    summary_variant.to_record(), sort_keys=True
                )
                for summary_allele in summary_variant.alleles:
                    extra_atts = {
                        "bucket_index": self.bucket_index,
                    }
                    summary_allele.summary_index = summary_variant_index
                    summary_allele.update_attributes(extra_atts)
                    summary_writer = self._get_bin_writer_summary(
                        summary_allele
                    )
                    summary_writer.append_summary_allele(
                        summary_allele, summary_blobs_json
                    )

            if summary_variant_index % 1000 == 0 and summary_variant_index > 0:
                elapsed = time.time() - self.start
                print(
                    f"Bucket {self.bucket_index}; "
                    f"{summary_variant.chromosome}:"
                    f"{summary_variant.position}: "
                    f"{summary_variant_index}/"
                    f"{family_variant_index} variants imported "
                    f"for {elapsed:.2f} sec ({len(self.data_writers)} files)",
                    file=sys.stderr,
                )

        filenames = list(self.data_writers.keys())

        for bin_writer in self.data_writers.values():
            bin_writer.close()

        print("-------------------------------------------", file=sys.stderr)
        print("Bucket:", self.bucket_index, file=sys.stderr)
        print("-------------------------------------------", file=sys.stderr)
        elapsed = time.time() - self.start
        print(
            f"DONE: {family_variant_index} family variants imported "
            f"for {elapsed:.2f} sec ({len(self.data_writers)} files)",
            file=sys.stderr,
        )
        print("-------------------------------------------", file=sys.stderr)

        return filenames

    def write_schema(self) -> None:
        """Write the schema to a separate file."""
        config: dict[str, Any] = {}

        schema_summary = self.serializer.schema_summary
        schema_family = self.serializer.schema_family
        config["summary_schema"] = {}
        config["family_schema"] = {}

        for k in schema_summary.names:
            v = schema_summary.field(k)
            config["summary_schema"][k] = str(v.type)

        for k in schema_family.names:
            v = schema_family.field(k)
            config["family_schema"][k] = str(v.type)

        filename = os.path.join(self.out_dir, "_VARIANTS_SCHEMA")

        config["extra_attributes"] = {}
        extra_attributes = self.serializer.extra_attributes
        for attr in extra_attributes:
            config["extra_attributes"][attr] = "string"

        with open(filename, "w") as configfile:
            content = toml.dumps(config)
            configfile.write(content)

    def write_partition(self) -> None:
        filename = os.path.join(self.out_dir, "_PARTITION_DESCRIPTION")
        with open(filename, "wt") as output:
            output.write(self.partition_descriptor.serialize())
            output.write("\n")

    def write_metadata(self) -> None:
        """Write dataset metadata."""
        schema_summary = "\n".join([
            f"{f.name}|{f.type}" for f in self.serializer.schema_summary
        ])
        schema_family = "\n".join([
            f"{f.name}|{f.type}" for f in self.serializer.schema_family
        ])
        extra_attributes = self.serializer.extra_attributes

        metadata_table = pa.Table.from_pydict(
            {
                "key": [
                    "partition_description",
                    "summary_schema",
                    "family_schema",
                    "extra_attributes",
                ],
                "value": [
                    self.partition_descriptor.serialize(),
                    str(schema_summary),
                    str(schema_family),
                    str(extra_attributes),
                ],
            },
            schema=pa.schema({"key": pa.string(), "value": pa.string()}),
        )
        metapath = fs_utils.join(self.out_dir, "meta", "meta.parquet")
        dirname = os.path.dirname(metapath)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname, exist_ok=True)

        pq.write_table(
            metadata_table,
            metapath,
            version="1.0"
        )

    def write_dataset(self) -> list[str]:
        filenames = self._write_internal()
        return filenames

    def write_meta(self) -> None:
        self.write_metadata()
        self.write_schema()
        self.write_partition()
