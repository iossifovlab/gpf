import pytest
import io
import re

from dae.backends.impala.parquet_io import ParquetPartitionDescriptor, \
    NoPartitionDescriptor
from dae.backends.impala.import_commons import MakefileGenerator


@pytest.mark.parametrize('region_length,chrom,bins_count', [
    (3_000_000_000, '1', 1),
    (3_000_000_000, '2', 1),
    (300_000_000, '1', 1),
    (300_000_000, '2', 1),
    (245_000_000, '1', 2),
    (245_000_000, '2', 1),
    (243_000_000, '2', 2),
    (243_199_373, '2', 1),
    (249_250_621, '1', 1)
])
def test_target_generator_region_bins_count(
        region_length, chrom, bins_count, genomes_db_2019):

    partition_descriptor = ParquetPartitionDescriptor(
            ['1', '2'], region_length)

    generator = MakefileGenerator(
        partition_descriptor,
        genomes_db_2019.get_genome())
    assert generator is not None
    assert generator.region_bins_count(chrom) == bins_count


@pytest.mark.parametrize('region_length,chrom,targets', [
    (3_000_000_000, '1', [('1_0', '1')]),
    (3_000_000_000, '3', [('other_0', '3')]),
    (3_000_000_000, 'X', [('other_0', 'X')]),
    (198_022_430, '3', [('other_0', '3')]),
    (100_000_000, '3', [
        ('other_0', '3:1-100000000'),
        ('other_1', '3:100000001-198022430')
    ]),
])
def test_target_generator_region_bins(
        region_length, chrom, targets, genomes_db_2019):

    partition_descriptor = ParquetPartitionDescriptor(
            ['1', '2'], region_length)

    generator = MakefileGenerator(
        partition_descriptor,
        genomes_db_2019.get_genome())

    assert generator is not None
    result = generator.generate_chrom_targets(chrom)
    print(result)
    assert targets == result


@pytest.mark.parametrize('region_length,target_chroms,targets', [
    (3_000_000_000, ('1', '2', '3'), ['3']),
    (3_000_000_000, ('3', ), ['3']),
    (3_000_000_000, ('3', 'X'), ['3', 'X']),
    (3_000_000, ('3', 'X'), ['3:1-3000000', 'X:1-3000000']),
])
def test_target_generator_other_0(
        region_length, target_chroms, targets, genomes_db_2019):

    partition_descriptor = ParquetPartitionDescriptor(
            ['1', '2'], region_length)

    generator = MakefileGenerator(
        partition_descriptor,
        genomes_db_2019.get_genome())

    result = generator.generate_variants_targets(target_chroms)
    print(result)
    assert result['other_0'] == targets


@pytest.mark.parametrize('region_length,targets', [
    (3_000_000_000, set(['1_0'])),
    (300_000_000, set(['1_0'])),
    (200_000_000, set(['1_0', '1_1'])),
    (50_000_000, set(['1_0', '1_1', '1_2', '1_3', '1_4', ])),
])
def test_target_generator_chrom_1(
        region_length, targets, genomes_db_2019):

    partition_descriptor = ParquetPartitionDescriptor(
            ['1', '2'], region_length)

    generator = MakefileGenerator(
        partition_descriptor,
        genomes_db_2019.get_genome())

    result = generator.generate_variants_targets(['1'])
    print(result)
    assert set(result.keys()) == targets


@pytest.mark.parametrize('region_length,targets', [
    (3_000_000_000, set(['other_0'])),
    (300_000_000, set(['other_0'])),
    (190_000_000, set(['other_0', 'other_1'])),
    (50_000_000, set(['other_0', 'other_1', 'other_2', 'other_3', ])),
])
def test_target_generator_chrom_other(
        region_length, targets, genomes_db_2019):

    partition_descriptor = ParquetPartitionDescriptor(
            ['1', '2'], region_length)

    generator = MakefileGenerator(
        partition_descriptor,
        genomes_db_2019.get_genome())
    print(generator.chromosome_lengths)

    result = generator.generate_variants_targets(['3', '4'])
    print(result)
    assert set(result.keys()) == targets


@pytest.mark.parametrize('region_length,target_chroms,all_bins', [
    (3_000_000_000, ('1', '3'), '1_0 other_0'),
    (240_000_000, ('1', '3'), '1_0 1_1 other_0'),
])
def test_generator_make_variants(
        region_length, target_chroms, all_bins, genomes_db_2019):

    partition_descriptor = ParquetPartitionDescriptor(
            ['1', '2'], region_length)

    generator = MakefileGenerator(
        partition_descriptor,
        genomes_db_2019.get_genome())

    output = io.StringIO()

    generator.generate_variants_make(
        'vcf2parquet.py ped.ped vcf.vcf --pd partition_description.conf',
        target_chroms, output=output)

    print(output.getvalue())
    search_string = f'all_bins={all_bins}'
    pattern = re.compile(search_string)
    assert pattern.search(output.getvalue())


def test_no_parition_description_simple(temp_filename, genomes_db_2019):
    partition_descriptor = NoPartitionDescriptor(temp_filename)

    generator = MakefileGenerator(
        partition_descriptor,
        genomes_db_2019.get_genome())

    output = io.StringIO()

    generator.generate_variants_make(
        'vcf2parquet.py ped.ped vcf.vcf',
        ('1'), output=output)

    print(output.getvalue())
