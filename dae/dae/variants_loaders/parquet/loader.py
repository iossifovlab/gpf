import os
import json
import glob
from collections.abc import Generator
from typing import Optional
import yaml
import numpy as np
from pyarrow import parquet as pq
from pyarrow import dataset as ds
from pyarrow import compute as pc
from dae.schema2_storage.schema2_import_storage import Schema2DatasetLayout, \
    schema2_dataset_layout
from dae.pedigrees.loader import FamiliesLoader
from dae.pedigrees.families_data import FamiliesData
from dae.variants.attributes import Inheritance, Role, Status, Sex
from dae.variants.variant import SummaryVariant, SummaryVariantFactory
from dae.variants.family_variant import FamilyVariant
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.utils.regions import Region


class ParquetLoaderException(Exception):
    pass


class ParquetHelper:
    """
    Helper class to incrementally fetch family variants.

    Important - this class assumes variants are ordered by their summary index.
    """

    columns = ("summary_index", "family_variant_data", "family_id")

    def __init__(self, path: str):
        self.pq_file = pq.ParquetFile(path)
        self.iterator = self.pq_file.iter_batches(
            columns=ParquetHelper.columns)
        self.batch: list[dict] = []
        self.exhausted = False

    @property
    def _current_idx(self) -> int:
        if not self.batch:
            return -1
        return int(self.batch[0]["summary_index"])

    def _advance(self) -> None:
        if self.exhausted:
            return
        try:
            self.batch = next(self.iterator).to_pylist()
        except StopIteration:
            self.exhausted = True

    def _pop(self) -> Optional[dict]:
        if self.exhausted:
            return None
        if not self.batch:
            self._advance()
        return self.batch.pop(0)

    def get(self, summary_idx: int) -> list[dict]:
        """Fetch all family variants matching the given summary index."""
        result: list[dict] = []

        if self.exhausted:
            return result
        if not self.batch:
            self._advance()

        if summary_idx < self._current_idx:
            return []
        while summary_idx > self._current_idx:
            rec = self._pop()  # seek forward
            if rec is None:
                return result
        while self._current_idx == summary_idx:
            rec = self._pop()
            if rec is None:
                return result
            result.append(rec)
        return result

    def close(self) -> None:
        self.pq_file.close()


class ParquetLoader:
    """Variants loader implementation for the Parquet format."""

    SUMMARY_COLUMNS = [
        "bucket_index", "summary_index", "allele_index",
        "summary_variant_data", "chromosome", "position",
    ]

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
            self.meta.get("partition_description", "").strip()
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
             else "other"), region.start, region.stop
        )
        rbin = ParquetLoader._extract_region_bin(path)
        bin_region = Region(
            rbin[0],
            (rbin[1] * self.partition_descriptor.region_length) + 1,
            (rbin[1] + 1) * self.partition_descriptor.region_length,
        )
        return bin_region.intersects(normalized_region)

    def get_summary_pq_filepaths(
        self, region: Optional[Region] = None
    ) -> tuple[str, ...]:
        """
        Produce a list of paths to available Parquet files.

        May filter by region (if region bins are configured).
        """
        summary_files = ds.dataset(f"{self.layout.summary}").files
        if region is not None \
           and self.partitioned \
           and self.partition_descriptor.has_region_bins():
            summary_files = [path for path in summary_files
                             if self._pq_file_in_region(path, region)]
        return tuple(summary_files)

    def get_family_pq_filepaths(self, summary_path: str) -> tuple[str, ...]:
        """Get all family parquet files for given summary parquet file."""
        if not self.layout.summary:
            raise ParquetLoaderException("No summary layout configured!")
        if not self.layout.family:
            raise ParquetLoaderException("No family layout configured!")
        if not os.path.exists(summary_path):
            raise ParquetLoaderException(
                f"Non-existent summary path given - {summary_path}")
        if not summary_path.startswith(self.layout.summary):
            raise ParquetLoaderException(
                f"Invalid summary path given - {summary_path}")
        bins = os.path.relpath(
            os.path.dirname(summary_path), self.layout.summary
        )
        glob_dir = os.path.join(
            self.layout.family, bins, "**", "*.parquet"
        )
        return tuple(glob.glob(glob_dir, recursive=True))

    def _deserialize_summary_variant(self, record: str) -> SummaryVariant:
        return SummaryVariantFactory.summary_variant_from_records(
            json.loads(record)
        )

    def _deserialize_family_variant(
        self, record: str, summary_variant: SummaryVariant
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
            inheritance_in_members=inheritance_in_members
        )

    def fetch_summary_variants(
        self, region: Optional[str] = None
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

        summary_paths = self.get_summary_pq_filepaths(region_obj)

        seen = set()

        for s_path in summary_paths:
            table = pq.read_table(
                s_path, columns=self.SUMMARY_COLUMNS, filters=region_filter)
            for rec in table.to_pylist():
                v_id = (rec["bucket_index"], rec["summary_index"])
                if v_id not in seen:
                    seen.add(v_id)
                    yield self._deserialize_summary_variant(
                        rec["summary_variant_data"]
                    )

    def fetch_variants(
        self, region: Optional[str] = None
    ) -> Generator[tuple[SummaryVariant, list[FamilyVariant]], None, None]:
        """Iterate over summary and family variants."""
        region_obj = None
        if region is not None:
            region_obj = Region.from_str(region)

        for s_path in self.get_summary_pq_filepaths(region_obj):
            s_pq = pq.ParquetFile(s_path)
            f_pqs = [ParquetHelper(path) for path
                     in self.get_family_pq_filepaths(s_path)]
            for batch in s_pq.iter_batches(columns=self.SUMMARY_COLUMNS):
                for rec in batch.to_pylist():
                    if region_obj is not None \
                       and not region_obj.contains(Region(rec["chromosome"],
                                                          rec["position"],
                                                          rec["position"])):
                        continue

                    sv_idx = rec["summary_index"]
                    sv = self._deserialize_summary_variant(
                        rec["summary_variant_data"])

                    fvs: list[dict] = []
                    for f_pq in f_pqs:
                        fvs.extend(f_pq.get(sv_idx))

                    to_yield = []
                    for fv in fvs:
                        to_yield.append(self._deserialize_family_variant(
                            fv["family_variant_data"], sv))
                    yield (sv, to_yield)

            s_pq.close()
            for f_pq in f_pqs:
                f_pq.close()
