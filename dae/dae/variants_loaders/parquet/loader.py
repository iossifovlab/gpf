import yaml
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

        self.has_annotation = bool(
            yaml.safe_load(self.meta.get("annotation_pipeline")))

        self.partitioned: bool = self.meta.get("partition_description").strip()
        self.partition_descriptor = PartitionDescriptor.parse_string(
            self.meta.get("partition_description")
        )

    @staticmethod
    def _extract_region_bin(path: str) -> str:
        # (...)/region_bin=chr1_0/(...)
        #                  ^~~~~^
        start = path.find("region_bin=") + 11
        end = path.find("/", start)
        return path[start:end]

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
        normalized_region = Region(
            (region.chrom
             if region.chrom in self.partition_descriptor.chromosomes
             else "other"), region.start, region.stop
        )
        file_region_bin = ParquetLoader._extract_region_bin(path).split('_')
        bin_chrom = file_region_bin[0]
        bin_region_idx = int(file_region_bin[1])
        bin_region = Region(
            bin_chrom,
            (bin_region_idx * self.partition_descriptor.region_length) + 1,
            (bin_region_idx+1) * self.partition_descriptor.region_length,
        )
        return bin_region.intersects(normalized_region)

    def _get_pq_filepaths(self, region: Optional[Region] = None) -> tuple[list[str], list[str]]:
        summary_files = ds.dataset(f"{self.layout.summary}").files
        family_files = ds.dataset(f"{self.layout.family}").files
        if region is not None \
           and self.partitioned \
           and self.partition_descriptor.has_region_bins:
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
            )
            if region.chrom != "other":
                region_filter = region_filter \
                    & (pc.field("chromosome") == region.chrom)

        summary_paths, _ = self._get_pq_filepaths(region)
        columns = (
            "bucket_index", "summary_index", "allele_index",
            "summary_variant_data", "chromosome", "position",
        )

        seen = set()

        for s_path in summary_paths:
            summary_parquet = pq.ParquetFile(s_path)
            table = summary_parquet.read(columns=columns)
            if region_filter is not None:
                table = table.filter(region_filter)
            for rec in table.to_pylist():
                v_id = (rec["bucket_index"], rec["summary_index"])
                if v_id not in seen:
                    seen.add(v_id)
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
            )
            if region.chrom != "other":
                region_filter = region_filter \
                    & (pc.field("chromosome") == region.chrom)

        filepaths = self._get_pq_filepaths(region)

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