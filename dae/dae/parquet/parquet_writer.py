from __future__ import annotations

import logging
import os

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from dae.annotation.annotation_pipeline import AttributeInfo
from dae.parquet import helpers as parquet_helpers
from dae.parquet.helpers import url_to_pyarrow_fs
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.parquet.schema2.serializers import build_summary_schema
from dae.pedigrees.families_data import FamiliesData
from dae.utils import fs_utils
from dae.variants.attributes import Role, Sex, Status

logger = logging.getLogger(__name__)


def pedigree_parquet_schema() -> pa.Schema:
    """Return the schema for pedigree parquet file."""
    fields: list[pa.Field] = [
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
        pa.field("member_index", pa.int32()),
    ]

    return pa.schema(fields)


def add_missing_parquet_fields(
    pps: pa.Schema, ped_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pa.Schema]:
    """Add missing parquet fields."""
    missing_fields = set(ped_df.columns.values) - set(pps.names)

    if "family_bin" in missing_fields:
        pps = pps.append(pa.field("family_bin", pa.int8()))
        missing_fields = missing_fields - {"family_bin"}

    rename = {}
    for column in missing_fields:
        name = column.lower().replace(".", "_")
        pps = pps.append(pa.field(name, pa.string()))
        rename[column] = name

    ped_df = ped_df.rename(columns=rename)
    missing_fields = {rename[col] for col in missing_fields}

    for column in missing_fields:
        ped_df[column] = ped_df[column].apply(str)

    return ped_df, pps


def collect_pedigree_parquet_schema(ped_df: pd.DataFrame) -> pa.Schema:
    """Build the pedigree parquet schema."""
    pps = pedigree_parquet_schema()
    _ped_df, pps = add_missing_parquet_fields(pps, ped_df)
    return pps


def fill_family_bins(
    families: FamiliesData,
    partition_descriptor: PartitionDescriptor | None = None,
) -> None:
    """Save families data into a parquet file."""
    if partition_descriptor is not None \
            and partition_descriptor.has_family_bins():
        for family in families.values():
            family_bin = partition_descriptor.make_family_bin(
                family.family_id)
            for person in family.persons.values():
                person.set_attr("family_bin", family_bin)
        families._ped_df = None  # noqa: SLF001 pylint: disable=W0212


def save_ped_df_to_parquet(
    ped_df: pd.DataFrame, filename: str,
    parquet_version: str | None = None,
) -> None:
    """Save ped_df as a parquet file named filename."""
    ped_df = ped_df.copy()

    ped_df.role = ped_df.role.apply(Role.to_value)
    ped_df.sex = ped_df.sex.apply(Sex.to_value)
    ped_df.status = ped_df.status.apply(Status.to_value)
    if "generated" not in ped_df:
        ped_df["generated"] = False
    if "layout" not in ped_df:
        ped_df["layout"] = None
    if "not_sequenced" not in ped_df:
        ped_df["not_sequenced"] = False

    pps = pedigree_parquet_schema()
    ped_df, pps = add_missing_parquet_fields(pps, ped_df)

    table = pa.Table.from_pandas(ped_df, schema=pps)
    filesystem, filename = url_to_pyarrow_fs(filename)

    pq.write_table(
        table, filename,
        filesystem=filesystem,
        version=parquet_version,  # type: ignore
    )


def merge_variants_parquets(
    partition_descriptor: PartitionDescriptor,
    variants_dir: str,
    partition: list[tuple[str, str]],
    row_group_size: int = 50_000,
    parquet_version: str | None = None,
) -> None:
    """Merge parquet files in variants_dir."""
    output_parquet_file = fs_utils.join(
        variants_dir,
        partition_descriptor.partition_filename(
            "merged", partition, bucket_index=None,
        ),
    )
    parquet_files = sorted(fs_utils.glob(
        fs_utils.join(variants_dir, "*.parquet"),
    ))

    is_output_in_input = \
        any(fn.endswith(output_parquet_file) for fn in parquet_files)
    if is_output_in_input:
        # a leftover file from a previous run. Remove from list of files.
        # we use endswith instead of == because of path normalization
        for i, filename in enumerate(parquet_files):
            if filename.endswith(output_parquet_file):
                parquet_files.pop(i)
                break

    if len(parquet_files) > 0:
        logger.info(
            "Merging %d files in %s", len(parquet_files), variants_dir,
        )
        parquet_helpers.merge_parquets(
            parquet_files, output_parquet_file,
            row_group_size=row_group_size,
            parquet_version=parquet_version)


def append_meta_to_parquet(
    meta_filename: str,
    key: list[str], value: list[str],
) -> None:
    """Append key-value pair to meta data parquet file."""
    dirname = os.path.dirname(meta_filename)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname, exist_ok=True)

    append_table = pa.table(
        {
            "key": key,
            "value": value,
        },
        schema=pa.schema({"key": pa.string(), "value": pa.string()}),
    )

    if not os.path.isfile(meta_filename):
        pq.write_table(append_table, meta_filename)
        return

    meta_table = pq.read_table(meta_filename)
    meta_table = pa.concat_tables([meta_table, append_table])
    pq.write_table(meta_table, meta_filename)


def serialize_summary_schema(
    annotation_attributes: list[AttributeInfo],
    partition_descriptor: PartitionDescriptor,
) -> str:
    """Serialize the summary schema."""
    summary_schema = build_summary_schema(
        annotation_attributes,
    )
    schema = [
        (f.name, f.type) for f in summary_schema
    ]
    schema.extend(
        list(partition_descriptor.summary_partition_schema()))
    return "\n".join([
        f"{n}|{t}" for n, t in schema
    ])
