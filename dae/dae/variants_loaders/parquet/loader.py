import json
import os
from collections.abc import Generator
from typing import Optional

import numpy as np
import yaml
from pyarrow import compute as pc
from pyarrow import dataset as ds
from pyarrow import parquet as pq

from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.loader import FamiliesLoader
from dae.schema2_storage.schema2_import_storage import (
    Schema2DatasetLayout,
    schema2_dataset_layout,
)
from dae.utils.regions import Region
from dae.variants.attributes import Inheritance, Role, Sex, Status
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryVariant, SummaryVariantFactory


class ParquetLoaderException(Exception):
    pass


class ParquetLoader:
    """Variants loader implementation for the Parquet format."""

    DATA_COLUMN = "summary_variant_data"

    def __init__(self, data_dir: str):
        self.data_dir: str = data_dir
        self.layout: Schema2DatasetLayout = schema2_dataset_layout(data_dir)

        if not os.path.exists(self.layout.pedigree):
            raise ParquetLoaderException(
                f"No pedigree file exists in {self.data_dir}!")
        if len(ds.dataset(f"{self.layout.summary}").files) <= 0:
            raise ParquetLoaderException(
                f"No summary variants exists in {self.data_dir}!")

        self.families: FamiliesData = self._load_families(self.layout.pedigree)

        meta_file = pq.ParquetFile(self.layout.meta)
        self.meta = {row["key"]: row["value"]
                     for row in meta_file.read().to_pylist()}
        meta_file.close()

        self.has_annotation = bool(
            yaml.safe_load(self.meta.get("annotation_pipeline", "").strip()))

        self.partitioned: bool = \
            self.meta.get("partition_description", "").strip()
        self.partition_descriptor = PartitionDescriptor.parse_string(
            self.meta.get("partition_description", "").strip(),
        )

    @staticmethod
    def _extract_region_bin(path: str) -> tuple[str, int]:
        # (...)/region_bin=chr1_0/(...)
        #                  ^~~~~^
        start = path.find("region_bin=") + 11
        end = path.find("/", start)
        rbin = path[start:end].split("_")
        return rbin[0], int(rbin[1])

    @staticmethod
    def _load_families(path: str) -> FamiliesData:
        parquet_file = pq.ParquetFile(path)
        ped_df = parquet_file.read().to_pandas()
        parquet_file.close()
        ped_df.role = ped_df.role.apply(Role.from_value)
        ped_df.sex = ped_df.sex.apply(Sex.from_value)
        ped_df.status = ped_df.status.apply(Status.from_value)
        ped_df.loc[ped_df.layout.isna(), "layout"] = None
        return FamiliesLoader.build_families_data_from_pedigree(ped_df)

    def _pq_file_in_region(self, path: str, region: Region) -> bool:
        if not self.partition_descriptor.has_region_bins():
            raise ParquetLoaderException(
                f"No region bins exist in {self.data_dir}!")

        normalized_region = Region(
            (region.chrom
             if region.chrom in self.partition_descriptor.chromosomes
             else "other"), region.start, region.stop,
        )
        rbin = ParquetLoader._extract_region_bin(path)
        bin_region = Region(
            rbin[0],
            (rbin[1] * self.partition_descriptor.region_length) + 1,
            (rbin[1] + 1) * self.partition_descriptor.region_length,
        )
        return bin_region.intersects(normalized_region)

    def get_pq_filepaths(
        self, region: Optional[Region] = None,
    ) -> tuple[list[str], list[str]]:
        """
        Produce a list of paths to available Parquet files.

        May filter by region (if region bins are configured).
        """
        summary_files = ds.dataset(f"{self.layout.summary}").files
        family_files = ds.dataset(f"{self.layout.family}").files
        if region is not None \
           and self.partitioned \
           and self.partition_descriptor.has_region_bins():
            summary_files = [path for path in summary_files
                             if self._pq_file_in_region(path, region)]
            family_files = [path for path in family_files
                            if self._pq_file_in_region(path, region)]
        return summary_files, family_files

    def _deserialize_summary_variant(self, record: str) -> SummaryVariant:
        return SummaryVariantFactory.summary_variant_from_records(
            json.loads(record),
        )

    def _deserialize_family_variant(
        self, record: str, summary_variant: SummaryVariant,
    ) -> FamilyVariant:
        fv_record = json.loads(record)
        inheritance_in_members = {
            int(k): [Inheritance.from_value(inh) for inh in v]
            for k, v in fv_record["inheritance_in_members"].items()
        }
        return FamilyVariant(
            summary_variant,
            self.families[fv_record["family_id"]],
            np.array(fv_record["genotype"]),
            np.array(fv_record["best_state"]),
            inheritance_in_members=inheritance_in_members,
        )

    def fetch_summary_variants(
        self, region: Optional[str] = None,
    ) -> Generator[SummaryVariant, None, None]:
        """Iterate over summary variants."""
        region_obj = None
        region_filter = None
        if region is not None:
            region_obj = Region.from_str(region)
            region_filter = (
                (pc.field("chromosome") == region_obj.chrom)
                & (pc.field("position") >= region_obj.start)
                & (pc.field("position") <= region_obj.stop)
            )

        summary_paths, _ = self.get_pq_filepaths(region_obj)
        columns = [
            "bucket_index", "summary_index", "allele_index",
            "summary_variant_data", "chromosome", "position",
        ]

        seen = set()

        for s_path in summary_paths:
            table = pq.read_table(
                s_path, columns=columns, filters=region_filter)
            for rec in table.to_pylist():
                v_id = (rec["bucket_index"], rec["summary_index"])
                if v_id not in seen:
                    seen.add(v_id)
                    yield self._deserialize_summary_variant(
                        rec["summary_variant_data"],
                    )

    def fetch_variants(
        self, region: Optional[str] = None,
    ) -> Generator[tuple[SummaryVariant, list[FamilyVariant]], None, None]:
        """Iterate over summary and family variants."""
        region_obj = None
        region_filter = None
        if region is not None:
            region_obj = Region.from_str(region)
            region_filter = (
                (pc.field("chromosome") == region_obj.chrom)
                & (pc.field("position") >= region_obj.start)
                & (pc.field("position") <= region_obj.stop)
            )

        filepaths = self.get_pq_filepaths(region_obj)

        idx_columns = ("summary_index", "allele_index")
        s_columns = ("summary_variant_data",
                     "chromosome", "position",
                     *idx_columns)
        f_columns = ("family_variant_data", "family_id", *idx_columns)

        summary_variants: list[tuple[str, SummaryVariant]] = []
        family_variant_recs: dict[str, list[str]] = {}

        for s_path in filepaths[0]:
            s_parquet = pq.ParquetFile(s_path)
            table = s_parquet.read(columns=s_columns)
            if region_filter is not None:
                table = table.filter(region_filter)
            for rec in table.to_pylist():
                if rec["allele_index"] == 1:
                    variant = self._deserialize_summary_variant(
                        rec["summary_variant_data"],
                    )
                    summary_variants.append((rec["summary_index"], variant))

            s_parquet.close()

        seen_fvs = set()  # TODO Is there a better way?
        for f_path in filepaths[1]:
            f_parquet = pq.ParquetFile(f_path)
            for f_rec in f_parquet.read(columns=f_columns).to_pylist():
                a = (f_rec["summary_index"], f_rec["family_id"])
                if a not in seen_fvs:
                    seen_fvs.add(a)
                    family_variant_recs.setdefault(
                        f_rec["summary_index"], [],
                    ).append(
                        f_rec["family_variant_data"],
                    )
            f_parquet.close()

        for summary_index, summary_variant in summary_variants:
            if summary_index in family_variant_recs:
                family_variants = [
                    self._deserialize_family_variant(f_rec, summary_variant)
                    for f_rec in family_variant_recs[summary_index]
                ]
            else:
                family_variants = []
            yield (summary_variant, family_variants)
