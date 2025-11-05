import glob
import os
import pathlib
from collections.abc import Generator, Iterable
from typing import ClassVar

import numpy as np
import yaml
from pyarrow import compute as pc
from pyarrow import dataset as ds
from pyarrow import parquet as pq

from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.parquet.schema2.serializers import VariantsDataSerializer
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

    def __init__(
        self,
        path: str,
        columns: Iterable[str],
        batch_size: int = 500,
    ):
        if "summary_index" not in columns or "bucket_index" not in columns:
            raise ValueError
        self.pq_file = pq.ParquetFile(path)
        self.iterator = self.pq_file.iter_batches(
            columns=list(columns),
            batch_size=batch_size,
        )
        self.batch: list[dict] = []
        self.exhausted = False

    def __del__(self) -> None:
        self.close()

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

    def _peek(self) -> dict | None:
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
    def __init__(
        self,
        dirs: Iterable[str],
        columns: Iterable[str],
        batch_size: int = 1000,
    ):
        self.readers = tuple(
            Reader(path, columns, batch_size=batch_size)
            for path in dirs
        )

    def __del__(self) -> None:
        self.close()

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

    SUMMARY_COLUMNS: ClassVar[list[str]] = [
        "bucket_index", "summary_index", "allele_index",
        "summary_variant_data", "chromosome", "position", "end_position",
    ]

    FAMILY_COLUMNS: ClassVar[list[str]] = [
        "bucket_index", "summary_index", "family_id", "family_variant_data",
    ]

    def __init__(
        self,
        layout: Schema2DatasetLayout,
        batch_size: int = 1000,
    ):
        self.layout = layout
        self.batch_size = batch_size

        if not os.path.exists(self.layout.pedigree):
            raise ParquetLoaderException(
                f"No pedigree file exists in {self.layout.study}!")

        self.families: FamiliesData = self._load_families(self.layout.pedigree)
        meta_file = pq.ParquetFile(self.layout.meta)
        self.meta = {row["key"]: row["value"]
                     for row in meta_file.read().to_pylist()}
        meta_file.close()

        self.has_annotation = bool(
            yaml.safe_load(self.meta.get("annotation_pipeline", "").strip()))

        self.partition_descriptor = PartitionDescriptor.parse_string(
            self.meta.get("partition_description", "").strip(),
        )

        self.serializer = VariantsDataSerializer.build_serializer()

        self.files_per_region = self._scan_region_bins()

        self.contigs: dict[str, int] = {}
        if self.meta.get("contigs"):
            self.contigs = {
                contig[0]: int(contig[1])
                for contig in [r.split("=") for r in
                               self.meta["contigs"].split(",")]
            }

    @staticmethod
    def load_from_dir(input_dir: str) -> "ParquetLoader":
        return ParquetLoader(load_schema2_dataset_layout(input_dir))

    def _scan_region_bins(self) -> dict[tuple[str, str], list[str]]:
        if not self.layout.summary:
            return {}

        if not self.partition_descriptor.has_region_bins():
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
    def _load_families(path: str) -> FamiliesData:
        parquet_file = pq.ParquetFile(path)
        ped_df = parquet_file.read().to_pandas()
        parquet_file.close()
        ped_df.role = ped_df.role.apply(  # pyright: ignore[reportCallIssue]
            Role.from_value)  # type: ignore
        ped_df.sex = ped_df.sex.apply(
            Sex.from_value)  # type: ignore
        ped_df.status = ped_df.status.apply(
            Status.from_value)  # type: ignore
        ped_df.loc[ped_df.layout.isna(), "layout"] = None
        return FamiliesLoader.build_families_data_from_pedigree(ped_df)

    def get_summary_pq_filepaths(
        self, region: Region | None = None,
    ) -> Generator[list[str], None, None]:
        """
        Produce paths to available Parquet files grouped by region.

        Can filter by region if region bins are configured.
        """
        if not self.layout.summary:
            return

        if not self.partition_descriptor.has_region_bins():
            yield list(ds.dataset(f"{self.layout.summary}").files)
            return

        if region is None:
            region_bins = list(self.files_per_region.keys())
        else:
            region_bins = [
                ("region_bin", r)
                for r in self.partition_descriptor.region_to_region_bins(
                    region, self.contigs)
            ]

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

    def _deserialize_summary_variant(self, record: bytes) -> SummaryVariant:
        return SummaryVariantFactory.summary_variant_from_records(
            self.serializer.deserialize_summary_record(record),
        )

    def _deserialize_family_variant(
        self, record: bytes, summary_variant: SummaryVariant,
    ) -> FamilyVariant:
        fv_record = self.serializer.deserialize_family_record(record)
        inheritance_in_members = {
            int(k): [Inheritance.from_value(inh) for inh in v]
            for k, v in fv_record["inheritance_in_members"].items()
        }
        return FamilyVariant(
            summary_variant,
            self.families[fv_record["family_id"]],
            family_id=fv_record["family_id"],
            member_ids=fv_record.get("member_ids"),
            genotype=np.array(fv_record["genotype"]),
            best_state=np.array(fv_record["best_state"]),
            inheritance_in_members=inheritance_in_members,
        )

    def fetch_summary_variants(
        self, region: Region | None = None,
    ) -> Generator[SummaryVariant, None, None]:
        """Iterate over summary variants."""
        region_filter = None
        if region is not None:
            region_filter = pc.field("chromosome") == region.chrom
            if region.start is not None:
                region_filter = (
                    region_filter & (pc.field("end_position") >= region.start)
                )
            if region.stop is not None:
                region_filter = (
                    region_filter & (pc.field("position") <= region.stop)
                )

        for summary_paths in self.get_summary_pq_filepaths(region):
            if not summary_paths:
                continue

            seen = set()
            summary_reader = MultiReader(
                summary_paths,
                self.SUMMARY_COLUMNS,
                batch_size=self.batch_size,
            )

            for alleles in summary_reader:
                rec = alleles[0]
                sv_idx = (rec["bucket_index"], rec["summary_index"])
                if sv_idx in seen:
                    continue

                if region is not None \
                    and not region.intersects(Region(rec["chromosome"],
                                                     rec["position"],
                                                     rec["end_position"])):
                    continue

                seen.add(sv_idx)

                yield self._deserialize_summary_variant(
                    rec["summary_variant_data"])

            summary_reader.close()

    def fetch_variants(
        self, region: Region | None = None,
    ) -> Generator[tuple[SummaryVariant, list[FamilyVariant]], None, None]:
        """Iterate over summary and family variants."""
        for summary_paths in self.get_summary_pq_filepaths(region):
            if not summary_paths:
                continue
            family_paths: list[str] = []
            for path in summary_paths:
                family_paths.extend(self.get_family_pq_filepaths(path))

            summary_reader = MultiReader(summary_paths,
                                         self.SUMMARY_COLUMNS,
                                         batch_size=self.batch_size)
            family_reader = MultiReader(family_paths,
                                        self.FAMILY_COLUMNS,
                                        batch_size=self.batch_size)

            for alleles in summary_reader:
                rec = alleles[0]
                if region is not None \
                    and not region.intersects(Region(rec["chromosome"],
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
        self, region: Region | None = None,
    ) -> Generator[FamilyVariant, None, None]:
        """Iterate over family variants."""
        for _, fvs in self.fetch_variants(region):
            yield from fvs
