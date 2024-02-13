import os
import json
import numpy as np
import pyarrow as pa
from typing import Generator, Optional
from pyarrow import parquet as pq
from dae.schema2_storage.schema2_import_storage import Schema2DatasetLayout, schema2_dataset_layout
from dae.pedigrees.loader import FamiliesLoader
from dae.pedigrees.families_data import FamiliesData
from dae.variants.attributes import Inheritance, Role, Status, Sex
from dae.variants.variant import SummaryVariant, SummaryVariantFactory
from dae.variants.family_variant import FamilyVariant


class ParquetLoader:
    DATA_COLUMN = "summary_variant_data"

    def __init__(self, data_dir: str):
        self.data_dir: str = data_dir
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

    def _get_pq_filepaths(self) -> tuple[str, str]:
        summary_pq_file = os.listdir(self.layout.summary)[0]
        family_pq_file = summary_pq_file.replace("summary", "family")
        return (
            f"{self.layout.summary}/{summary_pq_file}",
            f"{self.layout.family}/{family_pq_file}"
        )

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

    @staticmethod
    def _fv_matches_sv(fv_rec: dict, sv_rec: dict) -> bool:
        return (fv_rec["bucket_index"] == sv_rec["bucket_index"]
                and fv_rec["summary_index"] == sv_rec["summary_index"])
        
    def fetch_variants(self) -> Generator[tuple[SummaryVariant, list[FamilyVariant]], None, None]:
        assert self.families is not None

        s_path, f_path = self._get_pq_filepaths()
        summary_parquet = pq.ParquetFile(s_path)
        family_parquet = pq.ParquetFile(f_path)

        idx_columns = ("bucket_index", "summary_index", "allele_index")

        family_batches = family_parquet.iter_batches(columns=("family_variant_data", *idx_columns))
        f_batch = list()
        f_batch_idx = 0

        for batch in summary_parquet.iter_batches(columns=("summary_variant_data", *idx_columns)):
            for sv_rec in batch.to_pylist():
                if sv_rec["allele_index"] == 0 or sv_rec["allele_index"] > 1:
                    continue
                sv = self._deserialize_summary_variant(sv_rec[self.DATA_COLUMN])
                fvs = []
                while f_batch is not None:
                    if f_batch_idx == len(f_batch):
                        f_batch_idx = 0
                        try:
                            f_batch = next(family_batches).to_pylist()
                        except StopIteration:
                            f_batch = None
                            break
                    fv_rec = f_batch[f_batch_idx]
                    if not ParquetLoader._fv_matches_sv(fv_rec, sv_rec):
                        break
                    fvs.append(self._deserialize_family_variant(fv_rec["family_variant_data"], sv))
                    f_batch_idx += 1
                yield sv, fvs
        summary_parquet.close()
        family_parquet.close()