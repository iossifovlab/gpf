"""Provides Apache Parquet storage of genotype data."""
import os
import sys
import time
import logging
from typing import Optional, Dict, Any

from copy import copy
from urllib.parse import urlparse

import toml
from box import Box

import numpy as np

import pyarrow as pa
from pyarrow import fs as pa_fs
import pyarrow.parquet as pq

import fsspec

from dae.parquet.helpers import url_to_pyarrow_fs
from dae.utils import fs_utils
from dae.utils.variant_utils import GenotypeType
from dae.variants.family_variant import FamilyAllele, FamilyVariant, \
    calculate_simple_best_state
from dae.variants.variant import SummaryVariant, SummaryAllele
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.parquet.schema1.serializers import AlleleParquetSerializer


logger = logging.getLogger(__name__)


class ContinuousParquetFileWriter:
    """Class that writes to a output parquet file.

    This class automatically writes to a given parquet file when supplied
    enough data. Automatically dumps leftover data when closing into the file
    """

    def __init__(
            self, filepath, variant_loader, filesystem=None, rows=100_000):

        self.filepath = filepath
        extra_attributes = variant_loader.get_attribute("extra_attributes")
        logger.info(
            "using variant loader %s with annotation schema %s",
            variant_loader,
            variant_loader.annotation_schema)

        self.serializer = AlleleParquetSerializer(
            variant_loader.annotation_schema, extra_attributes
        )
        self.schema = self.serializer.schema

        if filesystem is not None:
            filesystem.create_dir(filepath)
            self.dirname = filepath
        else:
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
        return len(self._data["chromosome"])

    def build_table(self):
        table = pa.Table.from_pydict(self._data, self.schema)
        return table

    def _write_table(self):
        self._writer.write_table(self.build_table())
        self.data_reset()

    def append_allele(
            self, allele, variant_data,
            extra_attributes_data, summary_vectors):
        """Append the data for an entire variant to the buffer.

        :param list attributes: List of key-value tuples containing the data
        """
        assert self._data is not None

        data = self.serializer.build_allele_batch_dict(
            allele, variant_data, extra_attributes_data, summary_vectors)
        for k, v in self._data.items():
            v.extend(data[k])

        if self.size() >= self.rows:
            logger.info(
                "parquet writer %s data flushing at len %s",
                self.filepath, self.size())
            self._write_table()

    def close(self):
        logger.info(
            "closing parquet writer %s at len %s", self.dirname, self.size())

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
            bucket_index=None,
            rows=100_000,
            include_reference=True):
        self.out_dir = out_dir
        self.variants_loader = variants_loader
        self.families = variants_loader.families
        self.full_variants_iterator = variants_loader.full_variants_iterator()

        self.bucket_index = bucket_index
        self.rows = rows

        self.include_reference = include_reference

        self.start = time.time()
        self.data_writers = {}
        assert isinstance(partition_descriptor, PartitionDescriptor)
        self.partition_descriptor = partition_descriptor

        extra_attributes = self.variants_loader.get_attribute(
            "extra_attributes")
        self.serializer = AlleleParquetSerializer(
            self.variants_loader.annotation_schema, extra_attributes)

    @staticmethod
    def _setup_reference_allele(summary_variant, family):
        genotype = -1 * np.ones(shape=(2, len(family)), dtype=GenotypeType)
        best_state = calculate_simple_best_state(
            genotype, summary_variant.allele_count
        )

        ref_summary_allele = summary_variant.ref_allele
        reference_allele = FamilyAllele(ref_summary_allele, family, genotype,
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
            self.out_dir, partition)
        partition_filename = self.partition_descriptor.partition_filename(
            "variants", partition, self.bucket_index)
        return fs_utils.join(partition_directory, partition_filename)

    def _get_bin_writer(self, family_allele):
        filename = self._build_family_filename(family_allele)

        if filename not in self.data_writers:
            if urlparse(filename).scheme:
                filesystem, path = pa_fs.FileSystem.from_uri(filename)
            else:
                filesystem, path = None, filename

            self.data_writers[filename] = ContinuousParquetFileWriter(
                path,
                self.variants_loader,
                filesystem=filesystem,
                rows=self.rows,
            )
        return self.data_writers[filename]

    def _write_internal(self):
        # pylint: disable=too-many-locals
        family_variant_index = 0
        report = False
        for summary_variant_index, (summary_variant, family_variants) in \
                enumerate(self.full_variants_iterator):
            summary_alleles = summary_variant.alleles

            summary_blobs = self.serializer.serialize_summary_data(
                summary_alleles
            )

            scores_blob = self.serializer.serialize_scores_data(
                summary_alleles)

            for summary_allele in summary_alleles:
                extra_atts = {
                    "bucket_index": self.bucket_index,
                }
                summary_allele.update_attributes(extra_atts)

            summary_vectors = self.serializer.build_searchable_vectors_summary(
                summary_variant)

            for family_variant in family_variants:
                family_variant_index += 1

                fv = family_variant
                if family_variant.is_unknown():
                    # handle all unknown variants
                    unknown_variant = self._setup_all_unknown_variant(
                        summary_variant, family_variant.family_id
                    )
                    fv = unknown_variant
                    if -1 not in summary_vectors:
                        summary_vectors[-1] = copy(summary_vectors[0])
                        header = self.serializer.allele_batch_header
                        allele_index_idx = header.index("allele_index")
                        vectors = summary_vectors[-1]
                        for vector in vectors:
                            vector[allele_index_idx] = -1

                fv.summary_index = summary_variant_index
                fv.family_index = family_variant_index

                for family_allele in fv.alleles:
                    extra_atts = {
                        "bucket_index": self.bucket_index,
                        "family_index": family_variant_index
                    }
                    family_allele.update_attributes(extra_atts)

                alleles = fv.alt_alleles
                if self.include_reference or fv.is_reference():
                    alleles = fv.alleles

                variant_data = self.serializer.serialize_family_variant(
                    alleles, summary_blobs, scores_blob)
                assert variant_data is not None

                extra_attributes_data = \
                    self.serializer.serialize_extra_attributes(fv)
                for family_allele in alleles:
                    bin_writer = self._get_bin_writer(family_allele)
                    bin_writer.append_allele(
                        family_allele, variant_data,
                        extra_attributes_data, summary_vectors)

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

        schema = self.serializer.schema
        config["variants_schema"] = {}
        for k in schema.names:
            v = schema.field(k)
            config["variants_schema"][k] = str(v.type)

        schema = self.serializer.describe_blob_schema()
        config["blob"] = {}
        for k, v in schema.items():
            config["blob"][k] = v

        filename = os.path.join(
            self.out_dir, "_VARIANTS_SCHEMA")

        config["extra_attributes"] = {}
        extra_attributes = self.serializer.extra_attributes
        for attr in extra_attributes:
            config["extra_attributes"][attr] = "string"

        with fsspec.open(filename, "w") as configfile:
            content = toml.dumps(config)
            configfile.write(content)

    def write_partition(self):
        """Write dataset metadata."""
        filename = os.path.join(self.out_dir, "_PARTITION_DESCRIPTION")

        with fsspec.open(filename, "w") as configfile:
            configfile.write(self.partition_descriptor.serialize())

    def write_dataset(self):
        """Write the variants, parittion description and schema."""
        filenames = self._write_internal()

        self.write_partition()
        self.write_schema()

        self.variants_loader.close()

        return filenames


class ParquetManager:
    """Provide function for producing variants and pedigree parquet files."""

    @staticmethod
    def build_parquet_filenames(
            prefix, study_id=None, bucket_index=0, suffix=None):
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
        variant_filename = os.path.join(
            variants_dirname, f"{study_id}{filesuffix}_variants.parquet")

        pedigree_filename = os.path.join(
            prefix, "pedigree", f"{study_id}{filesuffix}_pedigree.parquet")

        conf = {
            "variants_dirname": variants_dirname,
            "variants": variant_filename,
            "pedigree": pedigree_filename,
        }

        return Box(conf, default_box=True)

    @staticmethod
    def families_to_parquet(
            families, pedigree_filename,
            partition_descriptor: Optional[PartitionDescriptor] = None):
        """Write a FamiliesData object into paquet."""
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
            variants_loader, partition_descriptor,
            bucket_index=1, rows=100_000, include_reference=False):
        """Read variants from variant_loader and store them in parquet."""
        # assert variants_loader.get_attribute("annotation_schema") is not None
        print(f"variants to parquet ({rows} rows)", file=sys.stderr)
        start = time.time()

        variants_writer = VariantsParquetWriter(
            out_dir,
            variants_loader,
            partition_descriptor,
            bucket_index=bucket_index,
            rows=rows,
            include_reference=include_reference)

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
    missing_fields = set([rename[col] for col in missing_fields])

    for column in missing_fields:
        ped_df[column] = ped_df[column].apply(str)

    return ped_df, pps


def save_ped_df_to_parquet(ped_df, filename, filesystem=None):
    """Convert pdf_df from a dataframe to parquet and store it in filename."""
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
