import os
import json
import glob
from collections.abc import Generator, Iterable
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
    Helper class to incrementally fetch variants.

    Important - this class assumes variants are ordered by their summary index.
    """

    def __init__(self, path: str, columns: Iterable[str]):
        self.pq_file = pq.ParquetFile(path)
        self.columns = columns
        self.iterator = self.pq_file.iter_batches(columns=self.columns)
        self.batch: list[dict] = []
        self.exhausted = False

    @property
    def current_idx(self) -> int:
        if not self.batch:
            return -1
        return int(self.batch[0]["summary_index"])

    def advance(self) -> None:
        if self.exhausted:
            return
        try:
            self.batch = next(self.iterator).to_pylist()
        except StopIteration:
            self.exhausted = True

    def _pop(self) -> Optional[dict]:
        if not self.batch:
            self.advance()
        if self.exhausted:
            return None
        return self.batch.pop(0)

    def get(self, summary_idx: int) -> list[dict]:
        """Fetch all variants matching the given summary index."""
        result: list[dict] = []

        if self.exhausted:
            return result
        if not self.batch:
            self.advance()

        if summary_idx < self.current_idx:
            return []
        while summary_idx > self.current_idx:
            rec = self._pop()  # seek forward
            if rec is None:
                return result
        while self.current_idx == summary_idx:
            rec = self._pop()
            if rec is None:
                return result
            result.append(rec)
        return result

    def close(self) -> None:
        self.pq_file.close()


class MultiFamilyReader:
    """Read family variants from all parquet files in a given directory."""

    def __init__(self, dirs: Iterable[str], columns: Iterable[str]):
        self.readers = [ParquetHelper(path, columns) for path in dirs]

    def get(self, summary_idx: int) -> list[dict]:
        result = []
        for reader in self.readers:
            result.extend(reader.get(summary_idx))
        return result

    def close(self) -> None:
        for reader in self.readers:
            reader.close()


class MultiSummaryReader:
    """Read summary variants from all parquet files in a given directory."""

    def __init__(self, dirs: Iterable[str], columns: Iterable[str]):
        self.readers = [ParquetHelper(path, columns) for path in dirs]
        for reader in self.readers:
            reader.advance()  # init all readers
        self.current_idx = self.readers[0].current_idx
        for reader in self.readers:
            self.current_idx = min(self.current_idx, reader.current_idx)

    @property
    def _exhausted(self) -> bool:
        return all(reader.exhausted for reader in self.readers)

    def __iter__(self) -> "MultiSummaryReader":
        return self

    def __next__(self) -> dict:
        if self._exhausted:
            raise StopIteration
        result = []
        for reader in self.readers:
            result.extend(reader.get(self.current_idx))
        self.current_idx += 1
        if not result:
            return self.__next__()  # go next if nothing found for this idx
        return result[0]  # we only need one allele for now

    def close(self) -> None:
        for reader in self.readers:
            reader.close()


class ParquetLoader:
    """Variants loader implementation for the Parquet format."""

    SUMMARY_COLUMNS = [
        "bucket_index", "summary_index", "allele_index",
        "summary_variant_data", "chromosome", "position",
    ]

    FAMILY_COLUMNS = [
        "summary_index", "family_id", "family_variant_data"
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

        summary_paths = self.get_summary_pq_filepaths(region_obj)
        family_paths: list[str] = []
        for path in summary_paths:
            family_paths.extend(self.get_family_pq_filepaths(path))

        summary_reader = MultiSummaryReader(summary_paths,
                                            self.SUMMARY_COLUMNS)
        family_reader = MultiFamilyReader(family_paths,
                                          self.FAMILY_COLUMNS)

        for rec in summary_reader:
            if region_obj is not None \
                and not region_obj.contains(Region(rec["chromosome"],
                                                   rec["position"],
                                                   rec["position"])):
                continue

            sv_idx = rec["summary_index"]
            sv = self._deserialize_summary_variant(
                rec["summary_variant_data"])

            fvs = family_reader.get(sv_idx)

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
