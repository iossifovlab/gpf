import os
import sys
import time
import logging
import json
from functools import reduce
from typing import Dict, Any, Optional

import toml
from box import Box

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from dae.parquet.helpers import url_to_pyarrow_fs
from dae.utils import fs_utils
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
            os.makedirs(dirname)
        self.dirname = dirname

        filesystem, filepath = url_to_pyarrow_fs(filepath, filesystem)
        self._writer = pq.ParquetWriter(
            filepath, self.schema, compression="snappy", filesystem=filesystem,
            version="1.0"
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

        pq.write_table(
            metadata_table, fs_utils.join(self.out_dir, "meta.parquet"),
            version="1.0"
        )

    def write_dataset(self):
        filenames = self._write_internal()
        self.write_metadata()
        self.write_schema()
        self.write_partition()
        return filenames


class ParquetManager:
    """Provide function for producing variants and pedigree parquet files."""

    @staticmethod
    def build_parquet_filenames(
        prefix, study_id=None, bucket_index=0, suffix=None
    ):
        """Build parquet filenames."""
        assert bucket_index >= 0

        basename = os.path.basename(os.path.abspath(prefix))
        if study_id is None:
            study_id = basename
        assert study_id

        if suffix is None and bucket_index == 0:
            filesuffix = ""
        elif bucket_index > 0 and suffix is None:
            filesuffix = f"_{bucket_index:0>6}"
        elif bucket_index == 0 and suffix is not None:
            filesuffix = f"{suffix}"
        else:
            filesuffix = f"_{bucket_index:0>6}{suffix}"

        variants_dirname = os.path.join(prefix, "variants")

        summary_filename = os.path.join(
            variants_dirname, f"{study_id}{filesuffix}_summary_alleles.parquet"
        )

        family_filename = os.path.join(
            variants_dirname, f"{study_id}{filesuffix}_family_alleles.parquet"
        )

        pedigree_filename = os.path.join(
            prefix, "pedigree", f"{study_id}{filesuffix}_pedigree.parquet"
        )

        conf = {
            "variants_dirname": variants_dirname,
            "family_alleles": family_filename,
            "summary_alleles": summary_filename,
            "pedigree": pedigree_filename,
        }

        return Box(conf, default_box=True)

    @staticmethod
    def families_to_parquet(
            families, pedigree_filename,
            partition_descriptor: Optional[PartitionDescriptor] = None):
        """Save families data into a parquet file."""
        if partition_descriptor is not None \
                and partition_descriptor.has_family_bins():
            for family in families.values():
                family_bin = partition_descriptor.make_family_bin(
                    family.family_id)
                for person in family.persons.values():
                    person.set_attr("family_bin", family_bin)
            families._ped_df = None  # pylint: disable=protected-access

        dirname = os.path.dirname(pedigree_filename)
        if dirname:
            os.makedirs(dirname, exist_ok=True)

        save_ped_df_to_parquet(families.ped_df, pedigree_filename)

    @staticmethod
    def variants_to_parquet(
        out_dir,
        variants_loader,
        partition_descriptor,
        bucket_index=1,
        rows=100_000,
        include_reference=False,
    ):
        """Read variants from variant_loader and store them in parquet."""
        # assert variants_loader.get_attribute("annotation_schema") is not None

        start = time.time()

        variants_writer = VariantsParquetWriter(
            out_dir,
            variants_loader,
            partition_descriptor,
            bucket_index=bucket_index,
            rows=rows,
            include_reference=include_reference,
        )

        variants_writer.write_dataset()
        elapsed = time.time() - start

        print(f"DONE: for {elapsed:.2f} sec", file=sys.stderr)


def pedigree_parquet_schema():
    """Return the schema for pedigree parquet file."""
    fields = [
        pa.field("family_id", pa.string()),
        pa.field("person_id", pa.string()),
        pa.field("dad_id", pa.string()),
        pa.field("mom_id", pa.string()),
        pa.field("sex", pa.int8()),
        pa.field("status", pa.int8()),
        pa.field("role", pa.int32()),
        pa.field("sample_id", pa.string()),
        pa.field("generated", pa.bool_()),
        pa.field("layout", pa.string()),
        pa.field("not_sequenced", pa.bool_()),
    ]

    return pa.schema(fields)


def add_missing_parquet_fields(pps, ped_df):
    """Add missing parquet fields."""
    missing_fields = set(ped_df.columns.values) - set(pps.names)

    if "family_bin" in missing_fields:
        pps = pps.append(pa.field("family_bin", pa.int8()))
        missing_fields = missing_fields - set(["family_bin"])

    rename = {}
    for column in missing_fields:
        name = column.lower().replace(".", "_")
        pps = pps.append(pa.field(name, pa.string()))
        rename[column] = name

    ped_df = ped_df.rename(columns=rename)
    missing_fields = [rename[col] for col in missing_fields]  # type: ignore

    for column in missing_fields:
        ped_df[column] = ped_df[column].apply(str)

    return ped_df, pps


def save_ped_df_to_parquet(ped_df, filename, filesystem=None):
    """Save ped_df as a parquet file named filename."""
    ped_df = ped_df.copy()

    ped_df.role = ped_df.role.apply(lambda r: r.value)
    ped_df.sex = ped_df.sex.apply(lambda s: s.value)
    ped_df.status = ped_df.status.apply(lambda s: s.value)
    if "generated" not in ped_df:
        ped_df["generated"] = False
    if "layout" not in ped_df:
        ped_df["layout"] = None
    if "not_sequenced" not in ped_df:
        ped_df["not_sequenced"] = False

    pps = pedigree_parquet_schema()
    ped_df, pps = add_missing_parquet_fields(pps, ped_df)

    table = pa.Table.from_pandas(ped_df, schema=pps)
    filesystem, filename = url_to_pyarrow_fs(filename, filesystem)
    pq.write_table(table, filename, filesystem=filesystem, version="1.0")
