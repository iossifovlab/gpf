import glob
import json
import os
import pathlib
from collections.abc import Generator, Iterable
from typing import Optional

import numpy as np
import yaml
from pyarrow import compute as pc
from pyarrow import dataset as ds
from pyarrow import parquet as pq

from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.loader import FamiliesLoader
from dae.schema2_storage.schema2_layout import (
    Schema2DatasetLayout,
    load_schema2_dataset_layout,
)
from dae.utils.regions import Region
from dae.variants.attributes import Inheritance, Role, Sex, Status
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryVariant, SummaryVariantFactory


class ParquetLoaderException(Exception):
    pass


class Reader:
    """
    Helper class to incrementally fetch variants.

    This class assumes variants are ordered by their bucket and summary index!
    """

    BATCH_SIZE = 5000

    def __init__(self, path: str, columns: Iterable[str]):
        if "summary_index" not in columns or "bucket_index" not in columns:
            raise ValueError
        self.pq_file = pq.ParquetFile(path)
        self.iterator = self.pq_file.iter_batches(
            columns=columns, batch_size=Reader.BATCH_SIZE)
        self.batch: list[dict] = []
        self.exhausted = False

    def __iter__(self) -> "Reader":
        return self

    def __next__(self) -> list[dict]:
        """Return next batch of variants with matching indices."""
        if self.exhausted:
            raise StopIteration
        result: list[dict] = []
        initial_idx = self.current_idx
        while self.current_idx == initial_idx:
            result.append(self._pop())
        return result

    @property
    def current_idx(self) -> tuple[int, int]:
        top = self._peek()
        if top is None:
            return (-1, -1)
        return int(top["bucket_index"]), int(top["summary_index"])

    def _advance(self) -> None:
        if self.exhausted:
            return
        try:
            self.batch = next(self.iterator).to_pylist()
        except StopIteration:
            self.exhausted = True

    def _peek(self) -> Optional[dict]:
        if not self.batch:
            self._advance()
        if self.exhausted:
            return None
        return self.batch[0]

    def _pop(self) -> dict:
        if self._peek() is None:
            raise IndexError
        return self.batch.pop(0)

    def close(self) -> None:
        self.pq_file.close()


class MultiReader:
    """
    Incrementally fetch variants from multiple files.

    This class assumes variants are ordered by their bucket and summary index!
    """
    def __init__(self, dirs: Iterable[str], columns: Iterable[str]):
        self.readers = tuple(Reader(path, columns) for path in dirs)

    def __iter__(self) -> "MultiReader":
        return self

    def __next__(self) -> list[dict]:
        if self._exhausted:
            raise StopIteration
        result = []
        iteration_idx = self.current_idx
        for reader in self.readers:
            if not reader.exhausted:
                while reader.current_idx == iteration_idx:
                    result.extend(next(reader))
        return result

    @property
    def _exhausted(self) -> bool:
        return all(reader.exhausted for reader in self.readers)

    @property
    def current_idx(self) -> tuple[int, int]:
        if self._exhausted:
            return (-1, -1)
        return min(reader.current_idx for reader in self.readers
                   if not reader.exhausted)

    def close(self) -> None:
        for reader in self.readers:
            reader.close()


class ParquetLoader:
    """Variants loader implementation for the Parquet format."""

    SUMMARY_COLUMNS = [  # noqa: RUF012
        "bucket_index", "summary_index", "allele_index",
        "summary_variant_data", "chromosome", "position", "end_position",
    ]

    FAMILY_COLUMNS = [  # noqa: RUF012
        "bucket_index", "summary_index", "family_id", "family_variant_data",
    ]

    def __init__(self, data_dir: str):
        self.data_dir: str = data_dir
        self.layout: Schema2DatasetLayout = \
            load_schema2_dataset_layout(data_dir)

        if not os.path.exists(self.layout.pedigree):
            raise ParquetLoaderException(
                f"No pedigree file exists in {self.data_dir}!")

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

        self.files_per_region = self._scan_region_bins()

        self.contigs: dict[str, int] = {}
        if self.meta.get("contigs"):
            self.contigs = {
                contig[0]: int(contig[1])
                for contig in [r.split("=") for r in
                               self.meta["contigs"].split(",")]
            }

    def _scan_region_bins(self) -> dict[tuple[str, str], list[str]]:
        if not self.layout.summary:
            return {}

        if not self.partitioned \
           or not self.partition_descriptor.has_region_bins():
            return {}

        result: dict[tuple[str, str], list[str]] = {}
        for path in ds.dataset(f"{self.layout.summary}").files:
            summary = str(pathlib.Path(path).relative_to(self.layout.summary))
            partitions = self.partition_descriptor.path_to_partitions(summary)
            region_partition = None
            for partition in partitions:
                if partition[0] == "region_bin":
                    region_partition = partition
            if region_partition is None:
                raise ValueError
            result.setdefault(region_partition, []).append(path)
        return result

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

    def get_summary_pq_filepaths(
        self, region: Optional[Region] = None,
    ) -> Generator[list[str], None, None]:
        """
        Produce paths to available Parquet files grouped by region.

        Can filter by region if region bins are configured.
        """
        if not self.layout.summary:
            return

        if not self.partitioned \
           or not self.partition_descriptor.has_region_bins():
            yield list(ds.dataset(f"{self.layout.summary}").files)
            return

        region_bins = self.partition_descriptor.region_to_bins(
            region, self.contigs,
        ) if region is not None else self.files_per_region.keys()

        for r_bin in region_bins:
            if r_bin in self.files_per_region:
                # check with if since some region bins may not exist
                # if no variants were written there
                yield self.files_per_region[r_bin]

    def get_family_pq_filepaths(self, summary_path: str) -> list[str]:
        """Get all family parquet files for given summary parquet file."""
        if not self.layout.summary or not self.layout.family:
            return []

        if not os.path.exists(summary_path):
            raise ParquetLoaderException(
                f"Non-existent summary path given - {summary_path}")
        if not summary_path.startswith(self.layout.summary):
            raise ParquetLoaderException(
                f"Invalid summary path given - {summary_path}")
        bins = os.path.relpath(
            os.path.dirname(summary_path), self.layout.summary,
        )
        glob_dir = os.path.join(
            self.layout.family, bins, "**", "*.parquet",
        )
        return glob.glob(glob_dir, recursive=True)

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
                & (pc.field("end_position") >= region_obj.start)
                & (pc.field("position") <= region_obj.stop)
            )

        for summary_paths in self.get_summary_pq_filepaths(region_obj):
            if not summary_paths:
                continue
            seen = set()
            for s_path in summary_paths:
                table = pq.read_table(
                    s_path, columns=self.SUMMARY_COLUMNS, filters=region_filter)
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
        if region is not None:
            region_obj = Region.from_str(region)

        for summary_paths in self.get_summary_pq_filepaths(region_obj):
            if not summary_paths:
                continue
            family_paths: list[str] = []
            for path in summary_paths:
                family_paths.extend(self.get_family_pq_filepaths(path))

            summary_reader = MultiReader(summary_paths, self.SUMMARY_COLUMNS)
            family_reader = MultiReader(family_paths, self.FAMILY_COLUMNS)

            for alleles in summary_reader:
                rec = alleles[0]
                if region_obj is not None \
                    and not region_obj.intersects(Region(rec["chromosome"],
                                                         rec["position"],
                                                         rec["end_position"])):
                    continue

                sv_idx = (rec["bucket_index"], rec["summary_index"])
                sv = self._deserialize_summary_variant(
                    rec["summary_variant_data"])

                fvs: list[dict] = []
                try:
                    while sv_idx > family_reader.current_idx:
                        next(family_reader)
                    fvs = next(family_reader)
                except StopIteration:
                    pass

                seen = set()
                to_yield = []
                for fv in fvs:
                    fv_id = (fv["summary_index"], fv["family_id"])
                    if fv_id not in seen:
                        seen.add(fv_id)
                        to_yield.append(self._deserialize_family_variant(
                            fv["family_variant_data"], sv))
                yield (sv, to_yield)

            summary_reader.close()
            family_reader.close()

    def fetch_family_variants(
        self, region: Optional[str] = None,
    ) -> Generator[FamilyVariant, None, None]:
        """Iterate over family variants."""
        for _, fvs in self.fetch_variants(region):
            yield from fvs
