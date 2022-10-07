# pylint: disable=W0621,C0114,C0116,W0212,W0613
from dataclasses import dataclass
import os
from box import Box  # type: ignore
import pytest
import pandas as pd
from fsspec.core import url_to_fs
from dae.impala_storage.schema2.schema2_genotype_storage import \
    Schema2GenotypeStorage
from dae.parquet.schema2.parquet_io import NoPartitionDescriptor


@dataclass(frozen=True)
class LocalLayout:
    pedigree_file: str
    variant_dir: str
    meta_file: str


@pytest.fixture
def import_layout(resources_dir, tmpdir) -> LocalLayout:
    sa_csv = pd.read_csv(resources_dir / "summary_alleles_table.csv")
    fa_csv = pd.read_csv(resources_dir / "family_alleles_table.csv")
    pedigree_csv = pd.read_csv(resources_dir / "pedigree_table.csv")
    meta_df = pd.DataFrame({"key": [], "value": []}, dtype=str)

    sa_dir, fa_dir = f"{tmpdir}/summary", f"{tmpdir}/family"
    os.makedirs(sa_dir)
    os.makedirs(fa_dir)
    sa_csv.to_parquet(sa_dir, partition_cols=["af_allele_count"])
    fa_csv.to_parquet(fa_dir, partition_cols=["allele_in_roles"])
    pedigree_fn = f"{tmpdir}/pedigree.parquet"
    pedigree_csv.to_parquet(pedigree_fn)
    meta_fn = f"{tmpdir}/meta.parquet"
    meta_df.to_parquet(meta_fn)

    return LocalLayout(pedigree_fn, tmpdir, meta_fn)


def test_hdfs_upload_dataset(import_layout):
    base_dir = "/user/test_user/studies"
    hdfs_host = os.environ.get("DAE_HDFS_HOST", "localhost")
    config = {
        "id": "genotype_impala",
        "storage_type": "impala2",
        "impala": {
            "db": "genotype_impala_db",
            "hosts": ["localhost"],
            "port": 21050,
            "pool_size": 3,
        },
        "hdfs": {
            "base_dir": base_dir,
            "host": hdfs_host,
            "port": 8020,
            "replication": 1,
        },
    }
    config = Box(config)
    partition_description = NoPartitionDescriptor(import_layout.variant_dir)
    hdfs, _ = url_to_fs(f"hdfs://{hdfs_host}:8020/")
    if hdfs.exists(base_dir):
        hdfs.rm(base_dir, recursive=True)  # cleanup from previous tests

    storage = Schema2GenotypeStorage(config)
    hdfs_layout = storage.hdfs_upload_dataset(
        "study_id", import_layout.variant_dir, import_layout.pedigree_file,
        import_layout.meta_file, partition_description)

    assert hdfs.exists(base_dir)
    assert hdfs.exists(hdfs_layout.family_variant_dir)
    assert hdfs.exists(hdfs_layout.summary_variant_dir)
    assert hdfs.exists(hdfs_layout.pedigree_file)
    assert hdfs.exists(hdfs_layout.summary_sample)
    assert hdfs.exists(hdfs_layout.family_sample)
    assert hdfs.exists(hdfs_layout.meta_file)
