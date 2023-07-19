# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
from dae.parquet.schema1.parquet_io import VariantsParquetWriter
from dae.parquet.partition_descriptor import PartitionDescriptor


PARTITION_STUDY_DATA = "backends/partition"


def test_region_partition(vcf_variants_loaders, temp_dirname):
    fvars = vcf_variants_loaders(PARTITION_STUDY_DATA)[0]

    partition_desc = PartitionDescriptor(
        ["1", "2"], 10000
    )

    parquet_writer = VariantsParquetWriter(
        temp_dirname, fvars, partition_desc)

    parquet_writer.write_dataset()

    assert os.path.exists(os.path.join(temp_dirname, "region_bin=1_86"))
    assert os.path.exists(os.path.join(temp_dirname, "region_bin=1_87"))
    assert os.path.exists(os.path.join(temp_dirname, "region_bin=1_90"))
    assert os.path.exists(os.path.join(temp_dirname, "region_bin=1_122"))
    assert os.path.exists(os.path.join(temp_dirname, "region_bin=2_86"))
    assert os.path.exists(os.path.join(temp_dirname, "region_bin=2_87"))
    assert os.path.exists(os.path.join(temp_dirname, "region_bin=2_90"))
    assert os.path.exists(os.path.join(temp_dirname, "region_bin=2_122"))
    assert os.path.exists(
        os.path.join(
            temp_dirname, "region_bin=1_86/variants_region_bin_1_86.parquet"
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname, "region_bin=2_87/variants_region_bin_2_87.parquet"
        )
    )


def test_region_partition_chromosome_filter(
        vcf_variants_loaders, temp_dirname):

    fvars = vcf_variants_loaders(PARTITION_STUDY_DATA)[0]

    partition_desc = PartitionDescriptor(
        ["1"], 10000)

    parquet_writer = VariantsParquetWriter(temp_dirname, fvars, partition_desc)
    parquet_writer.write_dataset()

    assert os.path.exists(os.path.join(temp_dirname, "region_bin=1_86"))
    assert os.path.exists(os.path.join(temp_dirname, "region_bin=1_87"))
    assert os.path.exists(os.path.join(temp_dirname, "region_bin=1_90"))
    assert os.path.exists(os.path.join(temp_dirname, "region_bin=1_122"))
    assert os.path.exists(os.path.join(temp_dirname, "region_bin=other_86"))
    assert os.path.exists(os.path.join(temp_dirname, "region_bin=other_87"))
    assert os.path.exists(os.path.join(temp_dirname, "region_bin=other_90"))
    assert os.path.exists(os.path.join(temp_dirname, "region_bin=other_122"))
    assert os.path.exists(
        os.path.join(
            temp_dirname, "region_bin=1_86/variants_region_bin_1_86.parquet"
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=other_87/variants_region_bin_other_87.parquet",
        )
    )


def test_region_partition_small_region(vcf_variants_loaders, temp_dirname):
    fvars = vcf_variants_loaders(PARTITION_STUDY_DATA)[0]

    partition_desc = PartitionDescriptor(["1", "2"], 10)

    parquet_writer = VariantsParquetWriter(temp_dirname, fvars, partition_desc)
    parquet_writer.write_dataset()

    assert os.path.exists(os.path.join(temp_dirname, "region_bin=1_86558"))
    assert os.path.exists(os.path.join(temp_dirname, "region_bin=1_86562"))
    assert os.path.exists(os.path.join(temp_dirname, "region_bin=1_86566"))
    assert os.path.exists(os.path.join(temp_dirname, "region_bin=1_86569"))
    assert os.path.exists(os.path.join(temp_dirname, "region_bin=1_87810"))
    assert os.path.exists(os.path.join(temp_dirname, "region_bin=1_90192"))
    assert os.path.exists(os.path.join(temp_dirname, "region_bin=1_90595"))
    assert os.path.exists(os.path.join(temp_dirname, "region_bin=1_122251"))
    assert os.path.exists(os.path.join(temp_dirname, "region_bin=2_86558"))
    assert os.path.exists(os.path.join(temp_dirname, "region_bin=2_86562"))
    assert os.path.exists(os.path.join(temp_dirname, "region_bin=2_86566"))
    assert os.path.exists(os.path.join(temp_dirname, "region_bin=2_86569"))
    assert os.path.exists(os.path.join(temp_dirname, "region_bin=2_87810"))
    assert os.path.exists(os.path.join(temp_dirname, "region_bin=2_90192"))
    assert os.path.exists(os.path.join(temp_dirname, "region_bin=2_90595"))
    assert os.path.exists(os.path.join(temp_dirname, "region_bin=2_122251"))
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=1_90595/variants_region_bin_1_90595.parquet",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=2_122251/variants_region_bin_2_122251.parquet",
        )
    )


def test_region_partition_large_region(vcf_variants_loaders, temp_dirname):
    fvars = vcf_variants_loaders(PARTITION_STUDY_DATA)[0]

    partition_desc = PartitionDescriptor(["1", "2"], 10000000)

    parquet_writer = VariantsParquetWriter(temp_dirname, fvars, partition_desc)
    parquet_writer.write_dataset()

    assert os.path.exists(os.path.join(temp_dirname, "region_bin=1_0"))
    assert os.path.exists(os.path.join(temp_dirname, "region_bin=2_0"))
    assert os.path.exists(
        os.path.join(
            temp_dirname, "region_bin=1_0/variants_region_bin_1_0.parquet"
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname, "region_bin=2_0/variants_region_bin_2_0.parquet"
        )
    )


def test_family_partition(vcf_variants_loaders, temp_dirname):
    fvars = vcf_variants_loaders(PARTITION_STUDY_DATA)[0]

    partition_desc = PartitionDescriptor(
        ["1", "2"], 10000000, 1000)

    parquet_writer = VariantsParquetWriter(temp_dirname, fvars, partition_desc)
    parquet_writer.write_dataset()

    assert os.path.exists(
        os.path.join(temp_dirname, "region_bin=1_0", "family_bin=369")
    )
    assert os.path.exists(
        os.path.join(temp_dirname, "region_bin=2_0", "family_bin=806")
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=1_0",
            "family_bin=369",
            "variants_region_bin_1_0_family_bin_369.parquet",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=1_0",
            "family_bin=806",
            "variants_region_bin_1_0_family_bin_806.parquet",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=2_0",
            "family_bin=369",
            "variants_region_bin_2_0_family_bin_369.parquet",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=2_0",
            "family_bin=806",
            "variants_region_bin_2_0_family_bin_806.parquet",
        )
    )


def test_coding_partition_1(vcf_variants_loaders, temp_dirname):
    fvars = vcf_variants_loaders(PARTITION_STUDY_DATA)[0]

    partition_desc = PartitionDescriptor(
        ["1", "2"],
        10000000,
        coding_effect_types=["missense"],
    )

    parquet_writer = VariantsParquetWriter(temp_dirname, fvars, partition_desc)
    parquet_writer.write_dataset()

    assert os.path.exists(
        os.path.join(temp_dirname, "region_bin=1_0", "coding_bin=1")
    )
    assert os.path.exists(
        os.path.join(temp_dirname, "region_bin=1_0", "coding_bin=0")
    )
    assert os.path.exists(
        os.path.join(temp_dirname, "region_bin=2_0", "coding_bin=0")
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=1_0",
            "coding_bin=0",
            "variants_region_bin_1_0_coding_bin_0.parquet",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=1_0",
            "coding_bin=1",
            "variants_region_bin_1_0_coding_bin_1.parquet",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=2_0",
            "coding_bin=0",
            "variants_region_bin_2_0_coding_bin_0.parquet",
        )
    )


def test_coding_partition_2(vcf_variants_loaders, temp_dirname):

    fvars = vcf_variants_loaders(PARTITION_STUDY_DATA)[0]
    partition_desc = PartitionDescriptor(
        ["1", "2"],
        10000000,
        coding_effect_types=[
            "missense",
            "nonsense",
            "synonymous",
            "frame-shift",
        ]
    )

    parquet_writer = VariantsParquetWriter(temp_dirname, fvars, partition_desc)
    parquet_writer.write_dataset()

    assert os.path.exists(
        os.path.join(temp_dirname, "region_bin=1_0", "coding_bin=1")
    )
    assert os.path.exists(
        os.path.join(temp_dirname, "region_bin=2_0", "coding_bin=0")
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=1_0",
            "coding_bin=1",
            "variants_region_bin_1_0_coding_bin_1.parquet",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=2_0",
            "coding_bin=0",
            "variants_region_bin_2_0_coding_bin_0.parquet",
        )
    )


def test_coding_partition_3(vcf_variants_loaders, temp_dirname):
    fvars = vcf_variants_loaders(PARTITION_STUDY_DATA)[0]

    partition_desc = PartitionDescriptor(
        ["1", "2"],
        10000000,
        coding_effect_types=["asdfghjkl"],
    )

    parquet_writer = VariantsParquetWriter(temp_dirname, fvars, partition_desc)
    parquet_writer.write_dataset()

    assert os.path.exists(
        os.path.join(temp_dirname, "region_bin=1_0", "coding_bin=0")
    )
    assert os.path.exists(
        os.path.join(temp_dirname, "region_bin=2_0", "coding_bin=0")
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=1_0",
            "coding_bin=0",
            "variants_region_bin_1_0_coding_bin_0.parquet",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=2_0",
            "coding_bin=0",
            "variants_region_bin_2_0_coding_bin_0.parquet",
        )
    )


def test_frequency_partition_1(vcf_variants_loaders, temp_dirname):
    fvars = vcf_variants_loaders(PARTITION_STUDY_DATA)[0]

    partition_desc = PartitionDescriptor(
        ["1", "2"], 10000000, rare_boundary=30)

    parquet_writer = VariantsParquetWriter(temp_dirname, fvars, partition_desc)
    parquet_writer.write_dataset()

    assert os.path.exists(
        os.path.join(temp_dirname, "region_bin=1_0", "frequency_bin=2")
    )
    assert os.path.exists(
        os.path.join(temp_dirname, "region_bin=1_0", "frequency_bin=3")
    )
    assert os.path.exists(
        os.path.join(temp_dirname, "region_bin=2_0", "frequency_bin=2")
    )
    assert os.path.exists(
        os.path.join(temp_dirname, "region_bin=2_0", "frequency_bin=3")
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=1_0",
            "frequency_bin=2",
            "variants_region_bin_1_0_frequency_bin_2.parquet",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=1_0",
            "frequency_bin=3",
            "variants_region_bin_1_0_frequency_bin_3.parquet",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=2_0",
            "frequency_bin=2",
            "variants_region_bin_2_0_frequency_bin_2.parquet",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=2_0",
            "frequency_bin=3",
            "variants_region_bin_2_0_frequency_bin_3.parquet",
        )
    )


def test_frequency_partition_2(vcf_variants_loaders, temp_dirname):
    fvars = vcf_variants_loaders(PARTITION_STUDY_DATA)[0]

    partition_desc = PartitionDescriptor(
        ["1", "2"], 10000000, rare_boundary=1
    )

    parquet_writer = VariantsParquetWriter(temp_dirname, fvars, partition_desc)
    parquet_writer.write_dataset()

    assert os.path.exists(
        os.path.join(temp_dirname, "region_bin=1_0", "frequency_bin=3")
    )
    assert os.path.exists(
        os.path.join(temp_dirname, "region_bin=2_0", "frequency_bin=3")
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=1_0",
            "frequency_bin=3",
            "variants_region_bin_1_0_frequency_bin_3.parquet",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=2_0",
            "frequency_bin=3",
            "variants_region_bin_2_0_frequency_bin_3.parquet",
        )
    )


def test_frequency_partition_3(vcf_variants_loaders, temp_dirname):
    fvars = vcf_variants_loaders(PARTITION_STUDY_DATA)[0]

    partition_desc = PartitionDescriptor(
        ["1", "2"], 10000000, rare_boundary=100
    )

    parquet_writer = VariantsParquetWriter(temp_dirname, fvars, partition_desc)
    parquet_writer.write_dataset()

    assert os.path.exists(
        os.path.join(temp_dirname, "region_bin=1_0", "frequency_bin=2")
    )
    assert os.path.exists(
        os.path.join(temp_dirname, "region_bin=2_0", "frequency_bin=2")
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=1_0",
            "frequency_bin=2",
            "variants_region_bin_1_0_frequency_bin_2.parquet",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=2_0",
            "frequency_bin=2",
            "variants_region_bin_2_0_frequency_bin_2.parquet",
        )
    )


def test_all(vcf_variants_loaders, temp_dirname):
    fvars = vcf_variants_loaders(PARTITION_STUDY_DATA)[0]

    partition_desc = PartitionDescriptor(
        ["1", "2"],
        100000,
        family_bin_size=100,
        coding_effect_types=[
            "missense",
            "nonsense",
            "frame-shift",
            "synonymous",
        ],
        rare_boundary=30,
    )

    parquet_writer = VariantsParquetWriter(temp_dirname, fvars, partition_desc)
    parquet_writer.write_dataset()

    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=1_8",
            "frequency_bin=2",
            "coding_bin=1",
            "family_bin=6",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=1_8",
            "frequency_bin=2",
            "coding_bin=1",
            "family_bin=69",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=1_9",
            "frequency_bin=2",
            "coding_bin=1",
            "family_bin=6",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=1_9",
            "frequency_bin=2",
            "coding_bin=1",
            "family_bin=69",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=1_12",
            "frequency_bin=3",
            "coding_bin=1",
            "family_bin=6",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=1_12",
            "frequency_bin=3",
            "coding_bin=1",
            "family_bin=69",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=2_8",
            "frequency_bin=2",
            "coding_bin=0",
            "family_bin=6",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=2_8",
            "frequency_bin=2",
            "coding_bin=0",
            "family_bin=69",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=2_9",
            "frequency_bin=2",
            "coding_bin=0",
            "family_bin=6",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=2_9",
            "frequency_bin=2",
            "coding_bin=0",
            "family_bin=69",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=2_12",
            "frequency_bin=3",
            "coding_bin=0",
            "family_bin=6",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=2_12",
            "frequency_bin=3",
            "coding_bin=0",
            "family_bin=69",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=1_9",
            "frequency_bin=2",
            "coding_bin=1",
            "family_bin=6",
            "variants_region_bin_1_9_frequency_bin_2_coding_bin_1"
            "_family_bin_6.parquet",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=2_12",
            "frequency_bin=3",
            "coding_bin=0",
            "family_bin=6",
            "variants_region_bin_2_12_frequency_bin_3_coding_bin_0"
            "_family_bin_6.parquet",
        )
    )


def test_region_family_frequency(vcf_variants_loaders, temp_dirname):
    fvars = vcf_variants_loaders(PARTITION_STUDY_DATA)[0]

    partition_desc = PartitionDescriptor(
        ["1", "2"],
        100000,
        family_bin_size=100,
        rare_boundary=30,
    )

    parquet_writer = VariantsParquetWriter(temp_dirname, fvars, partition_desc)
    parquet_writer.write_dataset()

    assert os.path.exists(
        os.path.join(
            temp_dirname, "region_bin=1_8", "frequency_bin=2", "family_bin=6",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname, "region_bin=1_8", "frequency_bin=2", "family_bin=69",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname, "region_bin=1_9", "frequency_bin=2", "family_bin=6",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname, "region_bin=1_9", "frequency_bin=2", "family_bin=69",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname, "region_bin=1_12", "frequency_bin=3", "family_bin=6",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=1_12",
            "frequency_bin=3",
            "family_bin=69",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname, "region_bin=2_8", "frequency_bin=2", "family_bin=6",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname, "region_bin=2_8", "frequency_bin=2", "family_bin=69",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname, "region_bin=2_9", "frequency_bin=2", "family_bin=6",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname, "region_bin=2_9", "frequency_bin=2", "family_bin=69",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname, "region_bin=2_12", "frequency_bin=3", "family_bin=6",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=2_12",
            "frequency_bin=3",
            "family_bin=69",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=1_9",
            "frequency_bin=2",
            "family_bin=6",
            "variants_region_bin_1_9_frequency_bin_2_family_bin_6.parquet",
        )
    )
    assert os.path.exists(
        os.path.join(
            temp_dirname,
            "region_bin=2_12",
            "frequency_bin=3",
            "family_bin=6",
            "variants_region_bin_2_12_frequency_bin_3_family_bin_6.parquet",
        )
    )
