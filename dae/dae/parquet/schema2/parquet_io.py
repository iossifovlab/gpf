import os
import sys
import time
import logging
import json
from dataclasses import dataclass
from functools import reduce
from typing import Dict, Any, Tuple
import toml

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from dae.utils import fs_utils
from dae.parquet.helpers import url_to_pyarrow_fs
from dae.utils.variant_utils import GenotypeType
from dae.variants.attributes import Inheritance
from dae.variants.family_variant import (
    FamilyAllele,
    FamilyVariant,
    calculate_simple_best_state,
)
from dae.variants.variant import SummaryVariant, SummaryAllele
from dae.parquet.schema2.serializers import AlleleParquetSerializer
from dae.parquet.partition_descriptor import PartitionDescriptor

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Schema2Layout:
    study_dir: str
    pedigree: str
    summary: str
    family: str
    meta: str


def schema2_layout(study_dir: str) -> Schema2Layout:
    return Schema2Layout(
        study_dir,
        fs_utils.join(study_dir, "pedigree", "pedigree.parquet"),
        fs_utils.join(study_dir, "summary"),
        fs_utils.join(study_dir, "family"),
        fs_utils.join(study_dir, "meta", "meta.parquet"))


def schema2_variants_layout(work_dir: str, study_id: str) -> Tuple[str, str]:
    study_dir = fs_utils.join(work_dir, study_id)
    return (
        fs_utils.join(study_dir, "summary"),
        fs_utils.join(study_dir, "family"),
    )


class ContinuousParquetFileWriter:
    """A continous parquet writer.

    Class that automatically writes to a given parquet file when supplied
    enough data. Automatically dumps leftover data when closing into the file
    """

    def __init__(
        self,
        filepath,
        variant_loader,
        filesystem=None,
        rows=100_000,
        schema="schema",
    ):

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
        self._data = None
        self.data_reset()

    def data_reset(self):
        self._data = {name: [] for name in self.schema.names}

    def size(self):
        assert self._data is not None
        return max(len(val) for val in self._data.values())

    def build_table(self):
        table = pa.Table.from_pydict(self._data, self.schema)
        return table

    def _write_table(self):
        self._writer.write_table(self.build_table())
        self.data_reset()

    def append_summary_allele(self, allele, json_data):
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

    def append_family_allele(self, allele, json_data):
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

    def close(self):
        logger.info(
            "closing parquet writer %s at len %d", self.dirname, self.size())

        if self.size() > 0:
            self._write_table()
        self._writer.close()


class VariantsParquetWriter:
    """Provide functions for storing variants into parquet dataset."""

    def __init__(
        self,
        out_dir,
        variants_loader,
        partition_descriptor,
        bucket_index=1,
        rows=100_000,
        include_reference=True,
        filesystem=None,
    ):
        self.out_dir = out_dir
        self.variants_loader = variants_loader
        self.families = variants_loader.families
        self.full_variants_iterator = variants_loader.full_variants_iterator()

        self.bucket_index = bucket_index
        self.rows = rows
        self.filesystem = filesystem

        self.include_reference = include_reference

        self.start = time.time()
        self.data_writers = {}
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

    @staticmethod
    def _setup_reference_allele(summary_variant, family):
        genotype = -1 * np.ones(shape=(2, len(family)), dtype=GenotypeType)
        best_state = calculate_simple_best_state(
            genotype, summary_variant.allele_count
        )

        ref_allele = summary_variant.ref_allele
        reference_allele = FamilyAllele(ref_allele, family, genotype,
                                        best_state)
        return reference_allele

    @staticmethod
    def _setup_all_unknown_allele(summary_variant, family):
        genotype = -1 * np.ones(shape=(2, len(family)), dtype=GenotypeType)
        best_state = calculate_simple_best_state(
            genotype, summary_variant.allele_count
        )

        ref_allele = summary_variant.ref_allele
        unknown_allele = FamilyAllele(
            SummaryAllele(
                ref_allele.chromosome,
                ref_allele.position,
                ref_allele.reference,
                ref_allele.reference,
                summary_index=ref_allele.summary_index,
                allele_index=-1,
                transmission_type=ref_allele.transmission_type,
                attributes={},
            ),
            family,
            genotype,
            best_state,
        )
        return unknown_allele

    def _setup_all_unknown_variant(self, summary_variant, family_id):
        family = self.families[family_id]
        genotype = -1 * np.ones(shape=(2, len(family)), dtype=GenotypeType)
        alleles = [
            self._setup_reference_allele(summary_variant, family),
            self._setup_all_unknown_allele(summary_variant, family),
        ]
        best_state = -1 * np.ones(
            shape=(len(alleles), len(family)), dtype=GenotypeType
        )
        return FamilyVariant(
            SummaryVariant(alleles), family, genotype, best_state
        )

    def _build_family_filename(self, allele):
        partition = self.partition_descriptor.family_partition(allele)
        partition_directory = self.partition_descriptor.partition_directory(
            fs_utils.join(self.out_dir, "family"), partition)
        partition_filename = self.partition_descriptor.partition_filename(
            "family", partition, self.bucket_index)
        return fs_utils.join(partition_directory, partition_filename)

    def _build_summary_filename(self, allele):
        partition = self.partition_descriptor.summary_partition(allele)
        partition_directory = self.partition_descriptor.partition_directory(
            fs_utils.join(self.out_dir, "summary"), partition)
        partition_filename = self.partition_descriptor.partition_filename(
            "summary", partition, self.bucket_index)
        return fs_utils.join(partition_directory, partition_filename)

    def _get_bin_writer_family(self, allele):
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

    def _get_bin_writer_summary(self, allele):
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

    def _write_internal(self):
        # pylint: disable=too-many-locals
        family_variant_index = 0
        report = False

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

                if fv.is_unknown() or fv.is_reference():
                    continue

                fv.summary_index = summary_variant_index
                fv.family_index = family_variant_index

                for fa in fv.alleles:
                    extra_atts = {
                        "bucket_index": self.bucket_index,
                        "family_index": family_variant_index,
                    }
                    fa.update_attributes(extra_atts)

                family_variant_data_json = json.dumps(fv.to_record,
                                                      sort_keys=True)

                for fa in fv.alt_alleles:
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
                    summary_variant.to_record, sort_keys=True
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

            if summary_variant_index % 1000 == 0:
                report = True

            if report:
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
                report = False

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

    def write_schema(self):
        """Write the schema to a separate file."""
        config: Dict[str, Any] = {}

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

    def write_partition(self):
        filename = os.path.join(self.out_dir, "_PARTITION_DESCRIPTION")
        with open(filename, "wt") as output:
            output.write(self.partition_descriptor.serialize())
            output.write("\n")

    def write_metadata(self):
        """Write dataset metadata."""
        schema_summary = self.serializer.schema_summary
        schema_family = self.serializer.schema_family
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

    def write_dataset(self):
        filenames = self._write_internal()
        self.write_metadata()
        self.write_schema()
        self.write_partition()
        return filenames
