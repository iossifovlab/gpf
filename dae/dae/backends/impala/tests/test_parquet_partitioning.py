import os
import shutil
from dae.backends.impala.parquet_io import VariantsParquetWriter
from dae.backends.impala.parquet_io import ParquetPartitionDescription


def test_region_partition(vcf_variants_loader):
    fvars = vcf_variants_loader('backends/partition')

    tmp_dir = '/tmp/dataset-partition-test'

    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)

    assert not os.path.exists(tmp_dir)
    os.mkdir(tmp_dir)

    partition_desc = ParquetPartitionDescription(['1', '2'], 10000)

    parquet_writer = VariantsParquetWriter(fvars, partition_desc,
                                           tmp_dir)

    assert parquet_writer is not None

    parquet_writer.write_partition()

    assert os.path.exists(os.path.join(tmp_dir, '1_86'))
    assert os.path.exists(os.path.join(tmp_dir, '1_87'))
    assert os.path.exists(os.path.join(tmp_dir, '1_90'))
    assert os.path.exists(os.path.join(tmp_dir, '1_122'))
    assert os.path.exists(os.path.join(tmp_dir, '2_86'))
    assert os.path.exists(os.path.join(tmp_dir, '2_87'))
    assert os.path.exists(os.path.join(tmp_dir, '2_90'))
    assert os.path.exists(os.path.join(tmp_dir, '2_122'))
    assert os.path.exists(
            os.path.join(tmp_dir,
                         '1_86/variants_region_bin_1_86.parquet'))
    assert os.path.exists(
            os.path.join(tmp_dir,
                         '2_87/variants_region_bin_2_87.parquet'))

    shutil.rmtree(tmp_dir)
    assert not os.path.exists(tmp_dir)


def test_region_partition_chromosome_filter(vcf_variants_loader):
    fvars = vcf_variants_loader('backends/partition')

    tmp_dir = '/tmp/dataset-partition-test'

    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)

    assert not os.path.exists(tmp_dir)
    os.mkdir(tmp_dir)

    partition_desc = ParquetPartitionDescription(['1'], 10000)

    parquet_writer = VariantsParquetWriter(fvars, partition_desc,
                                           tmp_dir)

    assert parquet_writer is not None

    parquet_writer.write_partition()

    assert os.path.exists(os.path.join(tmp_dir, '1_86'))
    assert os.path.exists(os.path.join(tmp_dir, '1_87'))
    assert os.path.exists(os.path.join(tmp_dir, '1_90'))
    assert os.path.exists(os.path.join(tmp_dir, '1_122'))
    assert os.path.exists(os.path.join(tmp_dir, 'other_86'))
    assert os.path.exists(os.path.join(tmp_dir, 'other_87'))
    assert os.path.exists(os.path.join(tmp_dir, 'other_90'))
    assert os.path.exists(os.path.join(tmp_dir, 'other_122'))
    assert os.path.exists(
            os.path.join(tmp_dir,
                         '1_86/variants_region_bin_1_86.parquet'))
    assert os.path.exists(
            os.path.join(tmp_dir,
                         'other_87/variants_region_bin_other_87.parquet'))

    shutil.rmtree(tmp_dir)
    assert not os.path.exists(tmp_dir)


def test_region_partition_small_region(vcf_variants_loader):
    fvars = vcf_variants_loader('backends/partition')

    tmp_dir = '/tmp/dataset-partition-test'

    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)

    assert not os.path.exists(tmp_dir)
    os.mkdir(tmp_dir)

    partition_desc = ParquetPartitionDescription(['1', '2'], 10)

    parquet_writer = VariantsParquetWriter(fvars, partition_desc,
                                           tmp_dir)

    assert parquet_writer is not None

    parquet_writer.write_partition()

    assert os.path.exists(os.path.join(tmp_dir, '1_86558'))
    assert os.path.exists(os.path.join(tmp_dir, '1_86562'))
    assert os.path.exists(os.path.join(tmp_dir, '1_86566'))
    assert os.path.exists(os.path.join(tmp_dir, '1_86569'))
    assert os.path.exists(os.path.join(tmp_dir, '1_87810'))
    assert os.path.exists(os.path.join(tmp_dir, '1_90192'))
    assert os.path.exists(os.path.join(tmp_dir, '1_90595'))
    assert os.path.exists(os.path.join(tmp_dir, '1_122251'))
    assert os.path.exists(os.path.join(tmp_dir, '2_86558'))
    assert os.path.exists(os.path.join(tmp_dir, '2_86562'))
    assert os.path.exists(os.path.join(tmp_dir, '2_86566'))
    assert os.path.exists(os.path.join(tmp_dir, '2_86569'))
    assert os.path.exists(os.path.join(tmp_dir, '2_87810'))
    assert os.path.exists(os.path.join(tmp_dir, '2_90192'))
    assert os.path.exists(os.path.join(tmp_dir, '2_90595'))
    assert os.path.exists(os.path.join(tmp_dir, '2_122251'))
    assert os.path.exists(
            os.path.join(tmp_dir,
                         '1_90595/variants_region_bin_1_90595.parquet'))
    assert os.path.exists(
            os.path.join(tmp_dir,
                         '2_122251/variants_region_bin_2_122251.parquet'))

    shutil.rmtree(tmp_dir)
    assert not os.path.exists(tmp_dir)


def test_region_partition_large_region(vcf_variants_loader):
    fvars = vcf_variants_loader('backends/partition')

    tmp_dir = '/tmp/dataset-partition-test'

    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)

    assert not os.path.exists(tmp_dir)
    os.mkdir(tmp_dir)

    partition_desc = ParquetPartitionDescription(['1', '2'], 10000000)

    parquet_writer = VariantsParquetWriter(fvars, partition_desc,
                                           tmp_dir)

    assert parquet_writer is not None

    parquet_writer.write_partition()

    assert os.path.exists(os.path.join(tmp_dir, '1_0'))
    assert os.path.exists(os.path.join(tmp_dir, '2_0'))
    assert os.path.exists(
            os.path.join(tmp_dir,
                         '1_0/variants_region_bin_1_0.parquet'))
    assert os.path.exists(
            os.path.join(tmp_dir,
                         '2_0/variants_region_bin_2_0.parquet'))

    shutil.rmtree(tmp_dir)
    assert not os.path.exists(tmp_dir)


def test_family_partition(vcf_variants_loader):
    fvars = vcf_variants_loader('backends/partition')

    tmp_dir = '/tmp/dataset-partition-test'

    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)

    assert not os.path.exists(tmp_dir)
    os.mkdir(tmp_dir)

    partition_desc = ParquetPartitionDescription(['1', '2'], 10000000, 1000)

    parquet_writer = VariantsParquetWriter(fvars, partition_desc,
                                           tmp_dir)

    assert parquet_writer is not None

    parquet_writer.write_partition()

    assert os.path.exists(os.path.join(tmp_dir, '1_0', '369'))
    assert os.path.exists(os.path.join(tmp_dir, '2_0', '806'))
    assert os.path.exists(
            os.path.join(tmp_dir,
                         '1_0',
                         '369',
                         'variants_region_bin_1_0_family_bin_369.parquet'))
    assert os.path.exists(
            os.path.join(tmp_dir,
                         '1_0',
                         '806',
                         'variants_region_bin_1_0_family_bin_806.parquet'))
    assert os.path.exists(
            os.path.join(tmp_dir,
                         '2_0',
                         '369',
                         'variants_region_bin_2_0_family_bin_369.parquet'))
    assert os.path.exists(
            os.path.join(tmp_dir,
                         '2_0',
                         '806',
                         'variants_region_bin_2_0_family_bin_806.parquet'))

    shutil.rmtree(tmp_dir)
    assert not os.path.exists(tmp_dir)


def test_coding_partition_1(vcf_variants_loader):
    fvars = vcf_variants_loader('backends/partition')

    tmp_dir = '/tmp/dataset-partition-test'

    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)

    assert not os.path.exists(tmp_dir)
    os.mkdir(tmp_dir)

    partition_desc = ParquetPartitionDescription(
            ['1', '2'], 10000000,
            coding_effect_types=['missense'])

    parquet_writer = VariantsParquetWriter(fvars, partition_desc,
                                           tmp_dir)

    assert parquet_writer is not None

    parquet_writer.write_partition()

    assert os.path.exists(os.path.join(tmp_dir, '1_0', '1'))
    assert os.path.exists(os.path.join(tmp_dir, '1_0', '0'))
    assert os.path.exists(os.path.join(tmp_dir, '2_0', '0'))
    assert os.path.exists(
            os.path.join(tmp_dir,
                         '1_0',
                         '0',
                         'variants_region_bin_1_0_coding_bin_0.parquet'))
    assert os.path.exists(
            os.path.join(tmp_dir,
                         '1_0',
                         '1',
                         'variants_region_bin_1_0_coding_bin_1.parquet'))
    assert os.path.exists(
            os.path.join(tmp_dir,
                         '2_0',
                         '0',
                         'variants_region_bin_2_0_coding_bin_0.parquet'))

    shutil.rmtree(tmp_dir)
    assert not os.path.exists(tmp_dir)


def test_coding_partition_2(vcf_variants_loader):
    fvars = vcf_variants_loader('backends/partition')

    tmp_dir = '/tmp/dataset-partition-test'

    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)

    assert not os.path.exists(tmp_dir)
    os.mkdir(tmp_dir)

    partition_desc = ParquetPartitionDescription(
            ['1', '2'], 10000000,
            coding_effect_types=[
                'missense', 'nonsense', 'synonymous', 'frame-shift'
            ])

    parquet_writer = VariantsParquetWriter(fvars, partition_desc,
                                           tmp_dir)

    assert parquet_writer is not None

    parquet_writer.write_partition()

    assert os.path.exists(os.path.join(tmp_dir, '1_0', '1'))
    assert os.path.exists(os.path.join(tmp_dir, '2_0', '0'))
    assert os.path.exists(
            os.path.join(tmp_dir,
                         '1_0',
                         '1',
                         'variants_region_bin_1_0_coding_bin_1.parquet'))
    assert os.path.exists(
            os.path.join(tmp_dir,
                         '2_0',
                         '0',
                         'variants_region_bin_2_0_coding_bin_0.parquet'))

    shutil.rmtree(tmp_dir)
    assert not os.path.exists(tmp_dir)


def test_coding_partition_3(vcf_variants_loader):
    fvars = vcf_variants_loader('backends/partition')

    tmp_dir = '/tmp/dataset-partition-test'

    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)

    assert not os.path.exists(tmp_dir)
    os.mkdir(tmp_dir)

    partition_desc = ParquetPartitionDescription(
            ['1', '2'], 10000000,
            coding_effect_types=['asdfghjkl'])

    parquet_writer = VariantsParquetWriter(fvars, partition_desc,
                                           tmp_dir)

    assert parquet_writer is not None

    parquet_writer.write_partition()

    assert os.path.exists(os.path.join(tmp_dir, '1_0', '0'))
    assert os.path.exists(os.path.join(tmp_dir, '2_0', '0'))
    assert os.path.exists(
            os.path.join(tmp_dir,
                         '1_0',
                         '0',
                         'variants_region_bin_1_0_coding_bin_0.parquet'))
    assert os.path.exists(
            os.path.join(tmp_dir,
                         '2_0',
                         '0',
                         'variants_region_bin_2_0_coding_bin_0.parquet'))

    shutil.rmtree(tmp_dir)
    assert not os.path.exists(tmp_dir)


def test_frequency_partition_1(vcf_variants_loader):
    fvars = vcf_variants_loader('backends/partition')

    tmp_dir = '/tmp/dataset-partition-test'

    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)

    assert not os.path.exists(tmp_dir)
    os.mkdir(tmp_dir)

    partition_desc = ParquetPartitionDescription(
            ['1', '2'], 10000000, rare_boundary=30)

    parquet_writer = VariantsParquetWriter(fvars, partition_desc,
                                           tmp_dir)

    assert parquet_writer is not None

    parquet_writer.write_partition()

    assert os.path.exists(os.path.join(tmp_dir, '1_0', '2'))
    assert os.path.exists(os.path.join(tmp_dir, '1_0', '3'))
    assert os.path.exists(os.path.join(tmp_dir, '2_0', '2'))
    assert os.path.exists(os.path.join(tmp_dir, '2_0', '3'))
    assert os.path.exists(
            os.path.join(tmp_dir,
                         '1_0',
                         '2',
                         'variants_region_bin_1_0_frequency_bin_2.parquet'))
    assert os.path.exists(
            os.path.join(tmp_dir,
                         '1_0',
                         '3',
                         'variants_region_bin_1_0_frequency_bin_3.parquet'))
    assert os.path.exists(
            os.path.join(tmp_dir,
                         '2_0',
                         '2',
                         'variants_region_bin_2_0_frequency_bin_2.parquet'))
    assert os.path.exists(
            os.path.join(tmp_dir,
                         '2_0',
                         '3',
                         'variants_region_bin_2_0_frequency_bin_3.parquet'))

    shutil.rmtree(tmp_dir)
    assert not os.path.exists(tmp_dir)


def test_frequency_partition_2(vcf_variants_loader):
    fvars = vcf_variants_loader('backends/partition')

    tmp_dir = '/tmp/dataset-partition-test'

    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)

    assert not os.path.exists(tmp_dir)
    os.mkdir(tmp_dir)

    partition_desc = ParquetPartitionDescription(
            ['1', '2'], 10000000, rare_boundary=1)

    parquet_writer = VariantsParquetWriter(fvars, partition_desc,
                                           tmp_dir)

    assert parquet_writer is not None

    parquet_writer.write_partition()

    assert os.path.exists(os.path.join(tmp_dir, '1_0', '3'))
    assert os.path.exists(os.path.join(tmp_dir, '2_0', '3'))
    assert os.path.exists(
            os.path.join(tmp_dir,
                         '1_0',
                         '3',
                         'variants_region_bin_1_0_frequency_bin_3.parquet'))
    assert os.path.exists(
            os.path.join(tmp_dir,
                         '2_0',
                         '3',
                         'variants_region_bin_2_0_frequency_bin_3.parquet'))

    shutil.rmtree(tmp_dir)
    assert not os.path.exists(tmp_dir)


def test_frequency_partition_3(vcf_variants_loader):
    fvars = vcf_variants_loader('backends/partition')

    tmp_dir = '/tmp/dataset-partition-test'

    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)

    assert not os.path.exists(tmp_dir)
    os.mkdir(tmp_dir)

    partition_desc = ParquetPartitionDescription(
            ['1', '2'], 10000000, rare_boundary=100)

    parquet_writer = VariantsParquetWriter(fvars, partition_desc,
                                           tmp_dir)

    assert parquet_writer is not None

    parquet_writer.write_partition()

    assert os.path.exists(os.path.join(tmp_dir, '1_0', '2'))
    assert os.path.exists(os.path.join(tmp_dir, '2_0', '2'))
    assert os.path.exists(
            os.path.join(tmp_dir,
                         '1_0',
                         '2',
                         'variants_region_bin_1_0_frequency_bin_2.parquet'))
    assert os.path.exists(
            os.path.join(tmp_dir,
                         '2_0',
                         '2',
                         'variants_region_bin_2_0_frequency_bin_2.parquet'))

    shutil.rmtree(tmp_dir)
    assert not os.path.exists(tmp_dir)


def test_all(vcf_variants_loader):
    fvars = vcf_variants_loader('backends/partition')

    tmp_dir = '/tmp/dataset-partition-test'

    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)

    assert not os.path.exists(tmp_dir)
    os.mkdir(tmp_dir)

    partition_desc = ParquetPartitionDescription(
            ['1', '2'], 100000,
            family_bin_size=100,
            coding_effect_types=[
                'missense', 'nonsense', 'frame-shift', 'synonymous'],
            rare_boundary=30)

    parquet_writer = VariantsParquetWriter(fvars, partition_desc,
                                           tmp_dir)

    assert parquet_writer is not None

    parquet_writer.write_partition()

    assert os.path.exists(os.path.join(
        tmp_dir,
        '1_8',
        '6',
        '1',
        '2'))
    assert os.path.exists(os.path.join(
        tmp_dir,
        '1_8',
        '69',
        '1',
        '2'))
    assert os.path.exists(os.path.join(
        tmp_dir,
        '1_9',
        '6',
        '1',
        '2'))
    assert os.path.exists(os.path.join(
        tmp_dir,
        '1_9',
        '69',
        '1',
        '2'))
    assert os.path.exists(os.path.join(
        tmp_dir,
        '1_12',
        '6',
        '1',
        '3'))
    assert os.path.exists(os.path.join(
        tmp_dir,
        '1_12',
        '69',
        '1',
        '3'))
    assert os.path.exists(os.path.join(
        tmp_dir,
        '2_8',
        '6',
        '0',
        '2'))
    assert os.path.exists(os.path.join(
        tmp_dir,
        '2_8',
        '69',
        '0',
        '2'))
    assert os.path.exists(os.path.join(
        tmp_dir,
        '2_9',
        '6',
        '0',
        '2'))
    assert os.path.exists(os.path.join(
        tmp_dir,
        '2_9',
        '69',
        '0',
        '2'))
    assert os.path.exists(os.path.join(
        tmp_dir,
        '2_12',
        '6',
        '0',
        '3'))
    assert os.path.exists(os.path.join(
        tmp_dir,
        '2_12',
        '69',
        '0',
        '3'))
    assert os.path.exists(
            os.path.join(tmp_dir,
                         '1_9',
                         '6',
                         '1',
                         '2',
                         'variants_region_bin_1_9_family_bin_6' +
                         '_coding_bin_1_frequency_bin_2.parquet'))
    assert os.path.exists(
            os.path.join(tmp_dir,
                         '2_12',
                         '6',
                         '0',
                         '3',
                         'variants_region_bin_2_12_family_bin_6' +
                         '_coding_bin_0_frequency_bin_3.parquet'))


def test_region_family_frequency(vcf_variants_loader):
    fvars = vcf_variants_loader('backends/partition')

    tmp_dir = '/tmp/dataset-partition-test'

    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)

    assert not os.path.exists(tmp_dir)
    os.mkdir(tmp_dir)

    partition_desc = ParquetPartitionDescription(
            ['1', '2'], 100000,
            family_bin_size=100,
            rare_boundary=30)

    parquet_writer = VariantsParquetWriter(fvars, partition_desc,
                                           tmp_dir)

    assert parquet_writer is not None

    parquet_writer.write_partition()

    assert os.path.exists(os.path.join(
        tmp_dir,
        '1_8',
        '6',
        '2'))
    assert os.path.exists(os.path.join(
        tmp_dir,
        '1_8',
        '69',
        '2'))
    assert os.path.exists(os.path.join(
        tmp_dir,
        '1_9',
        '6',
        '2'))
    assert os.path.exists(os.path.join(
        tmp_dir,
        '1_9',
        '69',
        '2'))
    assert os.path.exists(os.path.join(
        tmp_dir,
        '1_12',
        '6',
        '3'))
    assert os.path.exists(os.path.join(
        tmp_dir,
        '1_12',
        '69',
        '3'))
    assert os.path.exists(os.path.join(
        tmp_dir,
        '2_8',
        '6',
        '2'))
    assert os.path.exists(os.path.join(
        tmp_dir,
        '2_8',
        '69',
        '2'))
    assert os.path.exists(os.path.join(
        tmp_dir,
        '2_9',
        '6',
        '2'))
    assert os.path.exists(os.path.join(
        tmp_dir,
        '2_9',
        '69',
        '2'))
    assert os.path.exists(os.path.join(
        tmp_dir,
        '2_12',
        '6',
        '3'))
    assert os.path.exists(os.path.join(
        tmp_dir,
        '2_12',
        '69',
        '3'))
    assert os.path.exists(
            os.path.join(tmp_dir,
                         '1_9',
                         '6',
                         '2',
                         'variants_region_bin_1_9_family_bin_6' +
                         '_frequency_bin_2.parquet'))
    assert os.path.exists(
            os.path.join(tmp_dir,
                         '2_12',
                         '6',
                         '3',
                         'variants_region_bin_2_12_family_bin_6' +
                         '_frequency_bin_3.parquet'))
