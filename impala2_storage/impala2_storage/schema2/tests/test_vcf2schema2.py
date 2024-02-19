# pylint: disable=W0621,C0114,C0116,W0212,W0613

from glob import glob
import pathlib

import pandas as pd
import pytest

from dae.parquet.partition_descriptor import \
    PartitionDescriptor
from dae.gpf_instance.gpf_instance import GPFInstance

from impala2_storage.schema2.tests.conftest import run_vcf2schema2


@pytest.mark.parametrize("partition_description", [
    PartitionDescriptor(),
    PartitionDescriptor(chromosomes=["1"], region_length=5, family_bin_size=2),
])
def test_vcf2schema2(
    resources_dir: pathlib.Path,
    tmp_path: pathlib.Path,
    gpf_instance_2013: GPFInstance,
    partition_description: PartitionDescriptor
) -> None:
    variants_dir = str(tmp_path)

    # generate parquets
    run_vcf2schema2(
        variants_dir,
        str(resources_dir / "simple_variants.ped"),
        str(resources_dir / "simple_variants.vcf"),
        gpf_instance_2013, partition_description)

    family_parquets = glob(f"{variants_dir}/family/**/*.parquet",
                           recursive=True)
    assert len(family_parquets) >= 1

    summary_parquets = glob(f"{variants_dir}/summary/**/*.parquet",
                            recursive=True)
    assert len(summary_parquets) >= 1

    for file in family_parquets + summary_parquets:
        df = pd.read_parquet(file)
        assert len(df) > 0
