import os
import json
import numpy as np
import pyarrow as pa
from typing import Generator, Optional
from pyarrow import parquet as pq
from pyarrow import dataset as ds
from dae.schema2_storage.schema2_import_storage import Schema2DatasetLayout, schema2_dataset_layout
from dae.pedigrees.loader import FamiliesLoader
from dae.pedigrees.families_data import FamiliesData
from dae.variants.attributes import Inheritance, Role, Status, Sex
from dae.variants.variant import SummaryVariant, SummaryVariantFactory
from dae.variants.family_variant import FamilyVariant


class ParquetLoader:
    DATA_COLUMN = "summary_variant_data"

    def __init__(self, data_dir: str, partitioned: bool = False):
        self.data_dir: str = data_dir
        self.partitioned: bool = partitioned
        self.layout: Schema2DatasetLayout = schema2_dataset_layout(data_dir)
        self.families: Optional[FamiliesData] = None

    def load_families(self) -> None:
        parquet_file = pq.ParquetFile(self.layout.pedigree)
        ped_df = parquet_file.read().to_pandas()
        ped_df.role = ped_df.role.apply(Role.from_value)
        ped_df.sex = ped_df.sex.apply(Sex.from_value)
        ped_df.status = ped_df.status.apply(Status.from_value)
        ped_df.loc[ped_df.layout.isna(), "layout"] = None
        self.families = FamiliesLoader.build_families_data_from_pedigree(ped_df)
        parquet_file.close()

    def _get_pq_filepaths(self) -> tuple[list[str], list[str]]:
        summary_pq_file = os.listdir(self.layout.summary)[0]
        family_pq_file = summary_pq_file.replace("summary", "family")
        return [f"{self.layout.summary}/{summary_pq_file}"], [f"{self.layout.family}/{family_pq_file}"]

    def _get_partitioned_pq_filepaths(self) -> tuple[list[str], list[str]]:
        summary_files = ds.dataset(f"{self.layout.summary}").files
        family_files = ds.dataset(f"{self.layout.family}").files
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

    def fetch_summary_variants(self):
        # TODO implement region filter
        # TODO don't use fetch_variants
        pass

    def fetch_variants(self) -> Generator[tuple[SummaryVariant, list[FamilyVariant]], None, None]:
        # TODO implement region filter
        assert self.families is not None

        if self.partitioned:
            filepaths = self._get_partitioned_pq_filepaths()
        else:
            filepaths = self._get_pq_filepaths()

        idx_columns = ("bucket_index", "summary_index", "allele_index")
        summary_columns = ("summary_variant_data", *idx_columns)
        family_columns = ("family_variant_data", "family_id", *idx_columns)

        summary_variant_recs = []
        family_variant_recs = dict()

        for s_path in filepaths[0]:
            summary_parquet = pq.ParquetFile(s_path)
            for rec in summary_parquet.read(columns=summary_columns).to_pylist():
                if rec["allele_index"] == 1:
                    summary_variant_recs.append(rec)

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

        for s_rec in summary_variant_recs:
            summary_variant = self._deserialize_summary_variant(s_rec["summary_variant_data"])
            if s_rec["summary_index"] in family_variant_recs:
                family_variants = [
                    self._deserialize_family_variant(f_rec, summary_variant)
                    for f_rec in family_variant_recs[s_rec["summary_index"]]
                ]
            else:
                family_variants = []
            yield (summary_variant, family_variants)

        return