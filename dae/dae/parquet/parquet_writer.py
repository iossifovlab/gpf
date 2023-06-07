import os
import logging
from typing import Optional, Union, Type

import pyarrow as pa
import pyarrow.parquet as pq

from dae.utils import fs_utils
from dae.parquet import helpers as parquet_helpers
from dae.pedigrees.family import FamiliesData
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.parquet.helpers import url_to_pyarrow_fs
from dae.parquet.schema1.parquet_io import \
    VariantsParquetWriter as S1VariantsWriter
from dae.parquet.schema2.parquet_io import \
    VariantsParquetWriter as S2VariantsWriter

logger = logging.getLogger(__file__)


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
    missing_fields = set(rename[col] for col in missing_fields)

    for column in missing_fields:
        ped_df[column] = ped_df[column].apply(str)

    return ped_df, pps


def save_ped_df_to_parquet(ped_df, filename: str, filesystem=None):
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


class ParquetWriter:
    """Implement writing variants and pedigrees parquet files."""

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
        variants_writer_class: Type[
            Union[S1VariantsWriter, S2VariantsWriter]],
        bucket_index=1,
        rows=100_000,
        include_reference=False,
    ):
        """Read variants from variant_loader and store them in parquet."""
        variants_writer = variants_writer_class(
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
            out_dir,
            variants_loader,
            partition_description: PartitionDescriptor,
            bucket,
            project,
            variants_writer_class: Type[
                Union[S1VariantsWriter, S2VariantsWriter]]):
        """Write variants to the corresponding parquet files."""
        if bucket.region_bin is not None and bucket.region_bin != "none":
            logger.info(
                "resetting regions (rb: %s): %s",
                bucket.region_bin, bucket.regions)
            variants_loader.reset_regions(bucket.regions)

        rows = project.get_row_group_size(bucket)
        logger.debug("argv.rows: %s", rows)
        ParquetWriter.variants_to_parquet(
            out_dir,
            variants_loader,
            partition_description,
            variants_writer_class,
            bucket_index=bucket.index,
            rows=rows,
            include_reference=project.include_reference,
        )

    @staticmethod
    def write_meta(
            out_dir,
            variants_loader,
            partition_description: PartitionDescriptor,
            variants_writer_class: Type[
                Union[S1VariantsWriter, S2VariantsWriter]]):
        """Write dataset metadata."""
        variants_writer = variants_writer_class(
            out_dir,
            variants_loader,
            partition_description,
        )
        variants_writer.write_meta()

    @staticmethod
    def write_pedigree(
        output_filename: str,
        families: FamiliesData,
        partition_descriptor: PartitionDescriptor
    ) -> None:
        """Write FamiliesData to a pedigree parquet file."""
        ParquetWriter.families_to_parquet(
            families, output_filename, partition_descriptor)

    @staticmethod
    def merge_parquets(
        partition_descriptor: PartitionDescriptor,
        variants_dir: str,
        partitions: list[tuple[str, str]]
    ) -> None:
        """Mergee parquet files in variants_dir."""
        output_parquet_file = fs_utils.join(
            variants_dir,
            partition_descriptor.partition_filename(
                "merged", partitions, bucket_index=None
            )
        )
        parquet_files = fs_utils.glob(
            fs_utils.join(variants_dir, "*.parquet")
        )

        is_output_in_input = \
            any(fn.endswith(output_parquet_file) for fn in parquet_files)
        if is_output_in_input:
            # a leftover file from a previous run. Remove from list of files.
            # we use endswith instead of == because of path normalization
            for i, filename in enumerate(parquet_files):
                if filename.endswith(output_parquet_file):
                    parquet_files.pop(i)
                    break

        if len(parquet_files) > 1:
            logger.info(
                "Merging %d files in %s", len(parquet_files), variants_dir
            )
            parquet_helpers.merge_parquets(parquet_files, output_parquet_file)
