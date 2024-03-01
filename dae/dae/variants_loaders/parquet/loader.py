import json
import numpy as np
from typing import Generator, Optional
from pyarrow import parquet as pq
from pyarrow import dataset as ds
from pyarrow import compute as pc
from dae.schema2_storage.schema2_import_storage import Schema2DatasetLayout, schema2_dataset_layout
from dae.pedigrees.loader import FamiliesLoader
from dae.pedigrees.families_data import FamiliesData
from dae.variants.attributes import Inheritance, Role, Status, Sex
from dae.variants.variant import SummaryVariant, SummaryVariantFactory
from dae.variants.family_variant import FamilyVariant
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.utils.regions import Region


class ParquetLoader:
    DATA_COLUMN = "summary_variant_data"

    def __init__(self, data_dir: str):
        self.data_dir: str = data_dir
        self.layout: Schema2DatasetLayout = schema2_dataset_layout(data_dir)
        self.families: FamiliesData = self._load_families()

        meta_file = pq.ParquetFile(self.layout.meta)
        self.meta = { row["key"]: row["value"]
                      for row in meta_file.read().to_pylist() }
        meta_file.close()

        self.partitioned: bool = self.meta.get("partition_description").strip()
        self.partition_descriptor = PartitionDescriptor.parse_string(
            self.meta.get("partition_description")
        )

    @staticmethod
    def _extract_region_bin(path: str) -> str:
        return path[path.find("region_bin=")+11:path.find("frequency_bin=")-1]

    def get_contig_lengths(self) -> dict:
        result = {}
        summary_paths = ds.dataset(f"{self.layout.summary}").files

        if self.partitioned:
            all_region_bins = {ParquetLoader._extract_region_bin(path) for path in summary_paths}
            for contig in [*self.partition_descriptor.chromosomes, "other"]:
                contig_bins = {
                    bin.split("_")[1] for bin in all_region_bins if contig in bin
                }
                result[contig] = max(contig_bins) * self.partition_descriptor.region_length
        else:
            summary_parquet = pq.ParquetFile(summary_paths[0])
            table = summary_parquet.read(columns=["chromosome", "position"])
            contigs = set(table.column("chromosome").unique().to_pylist())
            for contig in contigs:
                largest = table.filter(pc.field("chromosome") == contig) \
                               .column("position") \
                               .sort(order="descending") \
                               .to_pylist()[0]
                result[contig] = largest + 1
        return result

    def _load_families(self) -> FamiliesData:
        parquet_file = pq.ParquetFile(self.layout.pedigree)
        ped_df = parquet_file.read().to_pandas()
        parquet_file.close()
        ped_df.role = ped_df.role.apply(Role.from_value)
        ped_df.sex = ped_df.sex.apply(Sex.from_value)
        ped_df.status = ped_df.status.apply(Status.from_value)
        ped_df.loc[ped_df.layout.isna(), "layout"] = None
        return FamiliesLoader.build_families_data_from_pedigree(ped_df)

    def _pq_file_in_region(self, path: str, region: Region) -> bool:
        assert self.partition_descriptor is not None

        # (...)/region_bin=chr1_0/frequency_bin=(...)
        #                  ^~~~~^
        # extract the region bin by finding where it begins in the path
        # and moving 11 characters forward (the length of "region_bin=")
        # analogous for the end index by finding "frequency_bin=".
        file_region_bin = ParquetLoader._extract_region_bin(path)
        # afterwards, check if the input region's start or stop positions fall inside the given region bin
        region_start_bin = self.partition_descriptor.make_region_bin(region.chrom, region.start)
        region_stop_bin = self.partition_descriptor.make_region_bin(region.chrom, region.stop)
        return (region_start_bin == file_region_bin
                or region_stop_bin == file_region_bin)

    def _get_pq_filepaths(self, region: Optional[Region] = None) -> tuple[list[str], list[str]]:
        summary_files = ds.dataset(f"{self.layout.summary}").files
        family_files = ds.dataset(f"{self.layout.family}").files
        if region is not None:
            summary_files = [path for path in summary_files
                             if self._pq_file_in_region(path, region)]
            family_files = [path for path in family_files
                            if self._pq_file_in_region(path, region)]
        return summary_files, family_files

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

    def fetch_summary_variants(self, region: str = None) -> Generator[SummaryVariant, None, None]:
        assert self.families is not None

        region_filter = None
        if region is not None:
            region = Region.from_str(region)
            region_filter = (
                (pc.field("position") >= region.start)
                & (pc.field("position") <= region.stop)
                & (pc.field("chromosome") == region.chrom)
            )

        summary_paths, _ = self._get_pq_filepaths()
        columns = ("summary_variant_data", "chromosome", "position", "allele_index")

        for s_path in summary_paths:
            summary_parquet = pq.ParquetFile(s_path)
            table = summary_parquet.read(columns=columns)
            if region_filter is not None:
                table = table.filter(region_filter)
            for rec in table.to_pylist():
                if rec["allele_index"] == 1:
                    yield self._deserialize_summary_variant(rec["summary_variant_data"])

            summary_parquet.close()

    def fetch_variants(
        self, region: str = None
    ) -> Generator[tuple[SummaryVariant, list[FamilyVariant]], None, None]:
        assert self.families is not None

        region_filter = None
        if region is not None:
            region = Region.from_str(region)
            region_filter = (
                (pc.field("position") >= region.start)
                & (pc.field("position") <= region.stop)
                & (pc.field("chromosome") == region.chrom)
            )

        filepaths = self._get_pq_filepaths()

        idx_columns = ("summary_index", "allele_index")
        summary_columns = ("summary_variant_data", "chromosome", "position", *idx_columns)
        family_columns = ("family_variant_data", "family_id", *idx_columns)

        summary_variants = []
        family_variant_recs = dict()

        for s_path in filepaths[0]:
            summary_parquet = pq.ParquetFile(s_path)
            table = summary_parquet.read(columns=summary_columns)
            if region_filter is not None:
                table = table.filter(region_filter)
            for rec in table.to_pylist():
                if rec["allele_index"] == 1:
                    variant = self._deserialize_summary_variant(rec["summary_variant_data"])
                    summary_variants.append((rec["summary_index"], variant))

            summary_parquet.close()

        seen_fvs = set()  # TODO Is there a better way?
        for f_path in filepaths[1]:
            family_parquet = pq.ParquetFile(f_path)
            for f_rec in family_parquet.read(columns=family_columns).to_pylist():
                a = (f_rec["summary_index"], f_rec["family_id"])
                if a not in seen_fvs:
                    seen_fvs.add(a)
                    family_variant_recs.setdefault(f_rec["summary_index"], list()).append(
                        f_rec["family_variant_data"]
                    )
            family_parquet.close()

        for summary_index, summary_variant in summary_variants:
            if summary_index in family_variant_recs:
                family_variants = [
                    self._deserialize_family_variant(f_rec, summary_variant)
                    for f_rec in family_variant_recs[summary_index]
                ]
            else:
                family_variants = []
            yield (summary_variant, family_variants)

        return