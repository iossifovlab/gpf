"""Provides Apache Parquet storage of genotype data."""
from __future__ import annotations

import os
import sys
import abc
import time
import logging
import functools
from copy import copy
from urllib.parse import urlparse

from typing import List, Union, Dict, Any, Optional, Callable
from typing_extensions import Protocol

import toml

import numpy as np
import pandas as pd
import pyarrow as pa
from pyarrow import fs as pa_fs
import pyarrow.parquet as pq

import fsspec

from dae.parquet.helpers import url_to_pyarrow_fs
from dae.utils import fs_utils
from dae.utils.variant_utils import GenotypeType
from dae.pedigrees.families_data import FamiliesData

from dae.variants.family_variant import FamilyAllele, FamilyVariant, \
    calculate_simple_best_state
from dae.variants.variant import SummaryVariant, SummaryAllele
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.parquet.parquet_writer import \
    save_ped_df_to_parquet, fill_family_bins
from dae.variants_loaders.raw.loader import VariantsLoader
from dae.pedigrees.family import Family
from dae.import_tools.import_tools import ImportProject, Bucket

from impala_storage.schema1.serializers import AlleleParquetSerializer


logger = logging.getLogger(__name__)


class AbstractVariantsParquetWriter(abc.ABC):
    """Abstract base class for parquet writes."""

    @abc.abstractmethod
    def write_schema(self) -> None:
        """Store the schema. Obsolete."""

    @abc.abstractmethod
    def write_partition(self) -> None:
        """Store the partition. Obsolete."""

    @abc.abstractmethod
    def write_metadata(self) -> None:
        """Store the dataset metadata into a meta parquet file."""

    @abc.abstractmethod
    def write_dataset(self) -> list[str]:
        """Store the variants parquet dataset."""

    @abc.abstractmethod
    def write_meta(self) -> None:
        """Store all the metadata. Obsolete."""

    @staticmethod
    @abc.abstractmethod
    def build_variants_writer(
        out_dir: str,
        variants_loader: VariantsLoader,
        partition_descriptor: PartitionDescriptor,
        bucket_index: int = 1,
        rows: int = 100_000,
        include_reference: bool = True,
        filesystem: Optional[fsspec.AbstractFileSystem] = None,
    ) -> AbstractVariantsParquetWriter:
        """Build a variants parquet writed."""

    @staticmethod
    @abc.abstractmethod
    def build_pedigree_writer() -> Callable[
            [pd.DataFrame, str, Optional[fsspec.AbstractFileSystem]], None]:
        """Build a variants parquet writer object."""


class ParquetWriterBuilder(Protocol):
    """Defines a parquet writer builder type protocol."""

    @staticmethod
    def build_variants_writer(
        out_dir: str,
        variants_loader: VariantsLoader,
        partition_descriptor: PartitionDescriptor,
        bucket_index: int = 1,
        rows: int = 100_000,
        include_reference: bool = True,
        filesystem: Optional[fsspec.AbstractFileSystem] = None,
    ) -> AbstractVariantsParquetWriter:
        """Build a variants parquet writer object."""

    @staticmethod
    def build_pedigree_writer() -> Callable[
            [pd.DataFrame, str, Optional[fsspec.AbstractFileSystem]], None]:
        """Build a variants parquet writer object."""


class ParquetWriter:
    """Implement writing variants and pedigrees parquet files."""

    @staticmethod
    def families_to_parquet(
        families: FamiliesData,
        pedigree_filename: str,
        parquet_writer_builder: ParquetWriterBuilder,
        partition_descriptor: Optional[PartitionDescriptor] = None,
    ) -> None:
        """Save families data into a parquet file."""
        fill_family_bins(families, partition_descriptor)

        dirname = os.path.dirname(pedigree_filename)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        pedigree_writer = parquet_writer_builder.build_pedigree_writer()
        pedigree_writer(families.ped_df, pedigree_filename, None)

    @staticmethod
    def variants_to_parquet(
        out_dir: str,
        variants_loader: VariantsLoader,
        partition_descriptor: PartitionDescriptor,
        parquet_writer_builder: ParquetWriterBuilder,
        bucket_index: int = 1,
        rows: int = 100_000,
        include_reference: bool = False,
    ) -> None:
        """Read variants from variant_loader and store them in parquet."""
        variants_writer = parquet_writer_builder.build_variants_writer(
            out_dir,
            variants_loader,
            partition_descriptor,
            bucket_index=bucket_index,
            rows=rows,
            include_reference=include_reference,
        )

        variants_writer.write_dataset()

    @staticmethod
    def write_variants(
        out_dir: str,
        variants_loader: VariantsLoader,
        partition_description: PartitionDescriptor,
        bucket: Bucket,
        project: ImportProject,
        parquet_writer_builder: ParquetWriterBuilder
    ) -> None:
        """Write variants to the corresponding parquet files."""
        if bucket.region_bin is not None and bucket.region_bin != "none":
            logger.info(
                "resetting regions (rb: %s): %s",
                bucket.region_bin, bucket.regions)
            variants_loader.reset_regions(bucket.regions)

        rows = project.get_row_group_size()
        logger.debug("argv.rows: %s", rows)
        ParquetWriter.variants_to_parquet(
            out_dir,
            variants_loader,
            partition_description,
            parquet_writer_builder,
            bucket_index=bucket.index,
            rows=rows,
            include_reference=project.include_reference,
        )

    @staticmethod
    def write_meta(
        out_dir: str,
        variants_loader: VariantsLoader,
        partition_description: PartitionDescriptor,
        parquet_writer_builder: ParquetWriterBuilder
    ) -> None:
        """Write dataset metadata."""
        variants_writer = parquet_writer_builder.build_variants_writer(
            out_dir,
            variants_loader,
            partition_description,
        )
        variants_writer.write_meta()

    @staticmethod
    def write_pedigree(
        output_filename: str,
        families: FamiliesData,
        partition_descriptor: PartitionDescriptor,
        parquet_writer_builder: ParquetWriterBuilder
    ) -> None:
        """Write FamiliesData to a pedigree parquet file."""
        ParquetWriter.families_to_parquet(
            families, output_filename,
            parquet_writer_builder,
            partition_descriptor,)


class ContinuousParquetFileWriter:
    """Class that writes to a output parquet file.

    This class automatically writes to a given parquet file when supplied
    enough data. Automatically dumps leftover data when closing into the file
    """

    def __init__(
        self, filepath: str,
        variant_loader: VariantsLoader,
        filesystem: Optional[fsspec.AbstractFileSystem] = None,
        rows: int = 100_000
    ) -> None:

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
                os.makedirs(dirname, exist_ok=True)
            self.dirname = dirname

        filesystem, filepath = url_to_pyarrow_fs(filepath, filesystem)
        self._writer = pq.ParquetWriter(
            filepath, self.schema, compression="snappy", filesystem=filesystem,
            version="1.0"
        )
        self.rows = rows
        self._data: Optional[dict[str, list]] = None
        self.data_reset()

    def data_reset(self) -> None:
        self._data = {name: [] for name in self.schema.names}

    def size(self) -> int:
        assert self._data is not None
        return len(self._data["chromosome"])

    def build_table(self) -> pa.Table:
        table = pa.Table.from_pydict(self._data, self.schema)
        return table

    def _write_table(self) -> None:
        self._writer.write_table(self.build_table())
        self.data_reset()

    def append_allele(
        self, allele: FamilyAllele, variant_data: bytes,
        extra_attributes_data: bytes,
        summary_vectors: dict[int, list]
    ) -> None:
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

    def close(self) -> None:
        logger.info(
            "closing parquet writer %s at len %s", self.dirname, self.size())

        if self.size() > 0:
            self._write_table()
        self._writer.close()


class VariantsParquetWriter(AbstractVariantsParquetWriter):
    """Provide functions for storing variants into parquet dataset."""

    def __init__(
        self,
        out_dir: str,
        variants_loader: VariantsLoader,
        partition_descriptor: PartitionDescriptor,
        bucket_index: Optional[int] = None,
        rows: int = 100_000,
        include_reference: bool = True
    ) -> None:
        self.out_dir = out_dir
        self.variants_loader = variants_loader
        self.families = variants_loader.families
        self.full_variants_iterator = variants_loader.full_variants_iterator()

        self.bucket_index = bucket_index
        self.rows = rows

        self.include_reference = include_reference

        self.start = time.time()
        self.data_writers: dict[str, ContinuousParquetFileWriter] = {}
        assert isinstance(partition_descriptor, PartitionDescriptor)
        self.partition_descriptor = partition_descriptor
        extra_attributes = self.variants_loader.get_attribute(
            "extra_attributes")
        self.serializer = AlleleParquetSerializer(
            self.variants_loader.annotation_schema, extra_attributes)

    @staticmethod
    def build_variants_writer(
        out_dir: str,
        variants_loader: VariantsLoader,
        partition_descriptor: PartitionDescriptor,
        bucket_index: int = 1,
        rows: int = 100_000,
        include_reference: bool = True,
        filesystem: Optional[fsspec.AbstractFileSystem] = None,
    ) -> AbstractVariantsParquetWriter:
        return VariantsParquetWriter(
            out_dir=out_dir,
            variants_loader=variants_loader,
            partition_descriptor=partition_descriptor,
            bucket_index=bucket_index,
            rows=rows,
            include_reference=include_reference,
        )

    @staticmethod
    def build_pedigree_writer() -> Callable[
            [pd.DataFrame, str, Optional[fsspec.AbstractFileSystem]], None]:
        """Build a variants parquet writer object."""
        return functools.partial(
            save_ped_df_to_parquet,
            parquet_version="1.0")

    @staticmethod
    def _setup_reference_allele(
        summary_variant: SummaryVariant,
        family: Family
    ) -> FamilyAllele:
        genotype = -1 * np.ones(shape=(2, len(family)), dtype=GenotypeType)
        best_state = calculate_simple_best_state(
            genotype, summary_variant.allele_count
        )

        ref_summary_allele = summary_variant.ref_allele
        reference_allele = FamilyAllele(ref_summary_allele, family, genotype,
                                        best_state)
        return reference_allele

    @staticmethod
    def _setup_all_unknown_allele(
        summary_variant: SummaryVariant,
        family: Family
    ) -> FamilyAllele:
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

    def _setup_all_unknown_variant(
        self, summary_variant: SummaryVariant,
        family_id: str
    ) -> FamilyVariant:
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
            SummaryVariant(alleles),  # type: ignore
            family, genotype, best_state
        )

    def _build_family_filename(self, allele: FamilyAllele) -> str:
        partition = self.partition_descriptor.schema1_partition(allele)
        partition_directory = self.partition_descriptor.partition_directory(
            self.out_dir, partition)
        partition_filename = self.partition_descriptor.partition_filename(
            "variants", partition, self.bucket_index)
        return fs_utils.join(partition_directory, partition_filename)

    def _get_bin_writer(
        self, family_allele: FamilyAllele
    ) -> ContinuousParquetFileWriter:
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

    def _write_internal(self) -> List[Union[str, Any]]:
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
                    alleles, summary_blobs, scores_blob)  # type: ignore
                assert variant_data is not None

                extra_attributes_data = \
                    self.serializer.serialize_extra_attributes(fv)
                for family_allele in alleles:
                    bin_writer = self._get_bin_writer(
                        family_allele)  # type: ignore
                    bin_writer.append_allele(
                        family_allele,  # type: ignore
                        variant_data,
                        extra_attributes_data,  # type: ignore
                        summary_vectors)

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

    def write_schema(self) -> None:
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

    def write_partition(self) -> None:
        """Write dataset metadata."""
        filename = os.path.join(self.out_dir, "_PARTITION_DESCRIPTION")

        with fsspec.open(filename, "w") as configfile:
            configfile.write(self.partition_descriptor.serialize())

    def write_dataset(self) -> List[Union[str, Any]]:
        """Write the variants, parittion description and schema."""
        filenames = self._write_internal()
        self.variants_loader.close()
        return filenames

    def write_meta(self) -> None:
        # TODO: This should be move to a different place so that these are
        # not written with every bucket.
        self.write_partition()
        self.write_schema()

    def write_metadata(self) -> None:
        """Write dataset metadata."""
