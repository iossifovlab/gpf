import json
import glob
from typing import Generator, Optional
from pyarrow import parquet as pq
from dae.schema2_storage.schema2_import_storage import Schema2DatasetLayout, schema2_dataset_layout
from dae.pedigrees.loader import FamiliesLoader
from dae.pedigrees.families_data import FamiliesData
from dae.variants.attributes import Role, Status, Sex
from dae.variants.variant import SummaryVariant, SummaryVariantFactory


class ParquetLoader:
    DATA_COLUMN = "summary_variant_data"

    def __init__(self, data_dir: str):
        self.data_dir: str = data_dir
        self.layout: Schema2DatasetLayout = schema2_dataset_layout(data_dir)
        self.families: Optional[FamiliesData] = None

    def _deserialize_summary_variant(self, record: str) -> SummaryVariant:
        return SummaryVariantFactory.summary_variant_from_records(
            json.loads(record)
        )

    def load_families(self) -> None:
        parquet_file = pq.ParquetFile(self.layout.pedigree)
        ped_df = parquet_file.read().to_pandas()
        ped_df.role = ped_df.role.apply(Role.from_value)
        ped_df.sex = ped_df.sex.apply(Sex.from_value)
        ped_df.status = ped_df.status.apply(Status.from_value)
        ped_df.loc[ped_df.layout.isna(), "layout"] = None
        self.families = FamiliesLoader.build_families_data_from_pedigree(ped_df)
        parquet_file.close()
        
    def fetch_variants(self) -> Generator[SummaryVariant, None, None]:
        assert self.families is not None
        for path in glob.glob(f"{self.layout.summary}/*.parquet"):
            parquet_file = pq.ParquetFile(path)
            for batch in parquet_file.iter_batches(columns=[self.DATA_COLUMN, "variant_type"]):
                for rec in batch.to_pylist():
                    if rec["variant_type"] == 0:  # skip ref alleles
                        continue
                    yield self._deserialize_summary_variant(rec[self.DATA_COLUMN])
            parquet_file.close()